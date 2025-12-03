import discord
import sqlite3
import asyncio
import dateparser
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from discord import app_commands
from discord import ui

# --- FORMULARIO ÚNICO ---
class TareaModal(ui.Modal, title="Nueva Tarea"):
    # Casilla 1: Descripción
    tarea = ui.TextInput(
        label="¿Qué tienes que hacer?",
        style=discord.TextStyle.paragraph,
        placeholder="Ej: Terminar el informe de laboratorio...",
        required=True,
        max_length=200
    )

    # Casilla 2: Fecha (Manual pero flexible)
    fecha = ui.TextInput(
        label="Fecha Límite (Opcional)",
        style=discord.TextStyle.short,
        placeholder="30/12/2025 14:00 | 30-12-2025 14:00 | Mañana a las 5pm",
        required=False,
        min_length=2,
        max_length=50
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        # Pedimos tiempo a Discord para procesar (evita error 404)
        await interaction.response.defer(ephemeral=False)

        contenido = self.tarea.value
        fecha_texto = self.fecha.value
        fecha_final_str = None

        if fecha_texto:
            dt = None
            
            # 1. INTENTO ESTRICTO (Formatos numéricos con / o -)
            formatos_validos = ["%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M", "%d/%m/%Y", "%d-%m-%Y"]
            
            for fmt in formatos_validos:
                try:
                    dt_temp = datetime.strptime(fecha_texto, fmt)
                    # Si solo puso fecha sin hora, asumimos fin del día (23:59)
                    if len(fecha_texto) <= 10: 
                        dt_temp = dt_temp.replace(hour=23, minute=59)
                    dt = dt_temp
                    break
                except ValueError:
                    continue

            # 2. INTENTO INTELIGENTE (Lenguaje Natural)
            if not dt:
                settings = {
                    'PREFER_DATES_FROM': 'future', 
                    'DATE_ORDER': 'DMY', 
                    'TIMEZONE': 'America/Santiago', # Ajusta a tu zona horaria real
                    'RETURN_AS_TIMEZONE_AWARE': False
                }
                dt = dateparser.parse(fecha_texto, languages=['es'], settings=settings)

            # 3. VERIFICACIÓN FINAL
            if not dt:
                await interaction.followup.send(
                    "❌ **Fecha no reconocida.**\nPrueba formatos como: `30-12-2025 14:00` o `Mañana a las 5pm`.", 
                    ephemeral=True
                )
                return

            if dt < datetime.now():
                await interaction.followup.send(
                    f"❌ La fecha **{dt.strftime('%d/%m/%Y %H:%M')}** ya pasó. Elige una futura.", 
                    ephemeral=True
                )
                return

            # Convertimos al formato estándar para la base de datos
            fecha_final_str = dt.strftime("%d/%m/%Y %H:%M")

        # Guardar en DB
        self.cog.add_task_db(interaction.user.id, contenido, fecha_final_str)

        msg_extra = f"\n📅 **Vence:** {fecha_final_str}" if fecha_final_str else ""
        await interaction.followup.send(f"💾 Tarea guardada:\n**{contenido}**{msg_extra}")

# --- COG PRINCIPAL ---
class Tareas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = 'herxin_memory.db'
        self.init_db()
        self.check_reminders.start()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS tareas (
                user_id INTEGER,
                contenido TEXT,
                fecha TEXT,
                avisado INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def add_task_db(self, user_id, contenido, fecha=None):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("INSERT INTO tareas (user_id, contenido, fecha, avisado) VALUES (?, ?, ?, 0)", 
                  (user_id, contenido, fecha))
        conn.commit()
        conn.close()

    def get_tasks_db(self, user_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT rowid, contenido, fecha FROM tareas WHERE user_id = ?", (user_id,))
        data = c.fetchall()
        conn.close()
        return data

    def delete_task_db(self, rowid, user_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("DELETE FROM tareas WHERE rowid = ? AND user_id = ?", (rowid, user_id))
        borrados = c.rowcount
        conn.commit()
        conn.close()
        return borrados > 0

    def mark_as_notified(self, rowid):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("UPDATE tareas SET avisado = 1 WHERE rowid = ?", (rowid,))
        conn.commit()
        conn.close()

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT rowid, user_id, contenido, fecha FROM tareas WHERE fecha IS NOT NULL AND avisado = 0")
        tareas = c.fetchall()
        conn.close()

        now = datetime.now()

        for tarea in tareas:
            row_id, user_id, contenido, fecha_str = tarea
            try:
                fecha_limite = datetime.strptime(fecha_str, "%d/%m/%Y %H:%M")
                if now >= (fecha_limite - timedelta(minutes=10)):
                    user = self.bot.get_user(user_id)
                    if user:
                        embed = discord.Embed(title="⏰ ¡Recordatorio!", color=0xff0000)
                        embed.add_field(name="Tarea", value=contenido, inline=False)
                        embed.add_field(name="Vence", value=fecha_str, inline=True)
                        embed.set_footer(text=f"ID: {row_id}")
                        try:
                            await user.send(embed=embed)
                        except:
                            pass
                    self.mark_as_notified(row_id)
            except ValueError:
                continue

    @check_reminders.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    # --- COMANDOS ---

    # CAMBIO REALIZADO: name="tarea" en lugar de "add"
    @app_commands.command(name="tarea", description="Crea una tarea nueva")
    async def tarea(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TareaModal(self))

    @app_commands.command(name="lista", description="Muestra tus tareas pendientes")
    async def lista(self, interaction: discord.Interaction):
        tareas = self.get_tasks_db(interaction.user.id)
        if not tareas:
            await interaction.response.send_message("📂 No tienes tareas pendientes.", ephemeral=True)
            return

        embed = discord.Embed(title=f"📝 Tareas de {interaction.user.name}", color=0xf1c40f)
        texto = ""
        for t in tareas:
            fecha_txt = f" (📅 {t[2]})" if t[2] else ""
            texto += f"**ID {t[0]}.** {t[1]}{fecha_txt}\n"
        
        embed.description = texto
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="done", description="Borra una tarea completada por su ID")
    async def done(self, interaction: discord.Interaction, id_tarea: int):
        exito = self.delete_task_db(id_tarea, interaction.user.id)
        if exito:
            await interaction.response.send_message(f"✅ Tarea **ID {id_tarea}** eliminada.")
        else:
            await interaction.response.send_message(f"❌ No encontré esa tarea.", ephemeral=True)

    @app_commands.command(name="pomodoro", description="Inicia un timer de estudio")
    async def pomodoro(self, interaction: discord.Interaction, minutos: int = 25):
        await interaction.response.send_message(f"🍅 **Pomodoro iniciado.** {minutos} minutos.")
        await asyncio.sleep(minutos * 60)
        await interaction.followup.send(f"🔔 {interaction.user.mention} **¡TIEMPO!** Hora del descanso.")

async def setup(bot):
    await bot.add_cog(Tareas(bot))