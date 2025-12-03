import discord
import asyncio
from datetime import timedelta
from discord.ext import commands
from discord import app_commands

class Utilidades(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- FUNCIÓN AUXILIAR PARA EL TIEMPO ---
    def convertir_tiempo(self, tiempo_str: str):
        """Convierte '10m', '1h', '1d' a un objeto timedelta"""
        unidad = tiempo_str[-1].lower()
        try:
            valor = int(tiempo_str[:-1])
        except ValueError:
            return None

        if unidad == 'm': return timedelta(minutes=valor)
        if unidad == 'h': return timedelta(hours=valor)
        if unidad == 'd': return timedelta(days=valor)
        return None

    @app_commands.command(name="ping", description="Verifica latencia")
    async def ping(self, interaction: discord.Interaction):
        latencia = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 **Pong!** Latencia: `{latencia}ms`")

    # --- COMANDO ANUNCIO (MEGÁFONO) ---
    @app_commands.command(name="anuncio", description="Envía un comunicado oficial destacado")
    @app_commands.describe(
        titulo="Título del anuncio",
        mensaje="Contenido del mensaje",
        canal="(Opcional) ¿Dónde enviarlo? (Por defecto: aquí)",
        mencion="(Opcional) ¿A quién notificar?"
    )
    @app_commands.choices(mencion=[
        app_commands.Choice(name="Nadie (Silencioso)", value="none"),
        app_commands.Choice(name="@everyone (Todos)", value="everyone"),
        app_commands.Choice(name="@here (Conectados)", value="here")
    ])
    @app_commands.checks.has_permissions(administrator=True) # Solo admins
    async def anuncio(self, interaction: discord.Interaction, 
                      titulo: str, 
                      mensaje: str, 
                      canal: discord.TextChannel = None,
                      mencion: app_commands.Choice[str] = None):
        
        # Si no elige canal, usamos el actual
        target_channel = canal or interaction.channel
        
        # Construimos la tarjeta (Embed)
        # Usamos negritas y un emoji fijo para darle impacto al título
        embed = discord.Embed(
            title=f"📢  {titulo.upper()}", 
            description=f"{mensaje}", 
            color=0xf1c40f # Color Dorado Brillante
        )
        
        # Footer elegante sin iconos extra
        embed.set_footer(text=f"Comunicado oficial de {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        # CAMBIO AQUÍ: Usamos el avatar del bot en lugar del megáfono
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Preparamos el texto de mención
        texto_mencion = ""
        if mencion:
            if mencion.value == "everyone":
                texto_mencion = "@everyone"
            elif mencion.value == "here":
                texto_mencion = "@here"

        try:
            # Enviamos el mensaje al canal destino
            await target_channel.send(content=texto_mencion, embed=embed)
            
            # Confirmamos al admin (solo él lo ve)
            await interaction.response.send_message(f"✅ Anuncio enviado correctamente a {target_channel.mention}.", ephemeral=True)
        
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ No tengo permisos para escribir en {target_channel.mention}.", ephemeral=True)

    # Manejo de errores específico para /anuncio
    @anuncio.error
    async def anuncio_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("🚫 **Acceso Denegado:** Este comando es solo para Administradores.", ephemeral=True)

# --- COMANDO LIMPIAR MEJORADO (QUIRÚRGICO) ---
    @app_commands.command(name="limpiar", description="Borra mensajes (Todos o de un usuario específico)")
    @app_commands.describe(
        cantidad="Cuántos mensajes revisar/borrar", 
        usuario="(Opcional) Borrar solo mensajes de esta persona"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def limpiar(self, interaction: discord.Interaction, cantidad: int, usuario: discord.Member = None):
        # Pedimos tiempo porque borrar muchos mensajes tarda un poco
        await interaction.response.defer(ephemeral=True) 

        if usuario:
            # MODO FRANCOTIRADOR: Borrar solo de un usuario
            # Definimos la condición: ¿Es el autor del mensaje el usuario señalado?
            def es_del_usuario(m):
                return m.author == usuario

            # purge usa el 'check' para filtrar
            deleted = await interaction.channel.purge(limit=cantidad, check=es_del_usuario)
            await interaction.followup.send(f"✅ Eliminados **{len(deleted)}** mensajes de {usuario.mention}.")
        
        else:
            # MODO GENERAL: Borrar todo lo que encuentre (como antes)
            deleted = await interaction.channel.purge(limit=cantidad)
            await interaction.followup.send(f"✅ Se borraron **{len(deleted)}** mensajes.")

    @limpiar.error
    async def limpiar_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("🚫 Necesitas permisos de 'Gestionar Mensajes'.", ephemeral=True)

    # --- COMANDO ENCUESTA ---
    @app_commands.command(name="encuesta", description="Crea una votación (Sí/No o Múltiples)")
    @app_commands.describe(pregunta="¿Qué quieres preguntar?", opciones="(Opcional) Separa con comas. Ej: Opción A, Opción B")
    async def encuesta(self, interaction: discord.Interaction, pregunta: str, opciones: str = None):
        if opciones is None:
            # Encuesta Simple
            embed = discord.Embed(title="📊 Encuesta", description=f"**{pregunta}**", color=0x3498db)
            embed.set_footer(text=f"Por: {interaction.user.display_name}")
            await interaction.response.send_message(embed=embed)
            mensaje = await interaction.original_response()
            await mensaje.add_reaction("👍")
            await mensaje.add_reaction("👎")
            return

        # Encuesta Múltiple
        lista = [x.strip() for x in opciones.split(",")]
        if len(lista) > 9:
            await interaction.response.send_message("❌ Máximo 9 opciones.", ephemeral=True)
            return

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        texto = ""
        for i, op in enumerate(lista):
            texto += f"{emojis[i]} {op}\n"

        embed = discord.Embed(title="📊 Encuesta Múltiple", description=f"**{pregunta}**\n\n{texto}", color=0x9b59b6)
        embed.set_footer(text=f"Por: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        
        mensaje = await interaction.original_response()
        for i in range(len(lista)):
            await mensaje.add_reaction(emojis[i])

    # --- COMANDO PERFIL ---
    @app_commands.command(name="perfil", description="Muestra tu ficha de usuario o la de un amigo")
    @app_commands.describe(usuario="¿De quién quieres ver la info? (Vacío = Tuya)")
    async def perfil(self, interaction: discord.Interaction, usuario: discord.Member = None):
        # Si no menciona a nadie, usa su propio perfil
        target = usuario or interaction.user
        
        embed = discord.Embed(title=f"👤 Perfil de {target.display_name}", color=target.color)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(name="🏷️ Nombre", value=f"`{target.name}`", inline=True)
        embed.add_field(name="🆔 ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="🤖 ¿Es Bot?", value="Sí" if target.bot else "No", inline=True)
        
        # Fechas con formato
        creado = target.created_at.strftime("%d/%m/%Y")
        unido = target.joined_at.strftime("%d/%m/%Y")
        
        embed.add_field(name="📅 Creó cuenta", value=creado, inline=True)
        embed.add_field(name="📥 Se unió al server", value=unido, inline=True)
        
        # Roles (menos el @everyone)
        roles = [r.mention for r in target.roles if r.name != "@everyone"]
        roles_str = ", ".join(roles) if roles else "Ninguno"
        embed.add_field(name="🛡️ Roles", value=roles_str, inline=False)
        
        await interaction.response.send_message(embed=embed)

    # --- COMANDO SILENCIAR (TIMEOUT) ---
    @app_commands.command(name="silenciar", description="Aísla a un usuario temporalmente (Timeout)")
    @app_commands.describe(
        usuario="¿A quién quieres castigar?", 
        tiempo="Duración (Ej: 10m, 1h, 1d)", 
        razon="¿Por qué?"
    )
    @app_commands.checks.has_permissions(moderate_members=True) # Permiso vital para aislar
    async def silenciar(self, interaction: discord.Interaction, usuario: discord.Member, tiempo: str, razon: str = "Sin motivo"):
        
        # Seguridad: No puedes silenciar a un admin o al propio bot
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ No puedes silenciar a alguien con igual o mayor rango que tú.", ephemeral=True)
            return

        duracion = self.convertir_tiempo(tiempo)
        if not duracion:
            await interaction.response.send_message("❌ Formato de tiempo inválido. Usa: `10m`, `1h` o `1d`.", ephemeral=True)
            return

        try:
            # Aplicamos el Timeout de Discord
            await usuario.timeout(duracion, reason=razon)
            
            embed = discord.Embed(title="🤫 Usuario Silenciado", color=0xff0000)
            embed.add_field(name="Usuario", value=usuario.mention, inline=True)
            embed.add_field(name="Tiempo", value=tiempo, inline=True)
            embed.add_field(name="Razón", value=razon, inline=False)
            embed.set_footer(text=f"Moderador: {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
            # (Opcional) Avisar al usuario por DM
            try:
                await usuario.send(f"🤐 Has sido silenciado en **{interaction.guild.name}** por **{tiempo}**. Razón: {razon}")
            except:
                pass

        except discord.Forbidden:
            await interaction.response.send_message("❌ No tengo permisos para silenciar a este usuario (¿Es el dueño o tiene un rol más alto que yo?).", ephemeral=True)

    # --- COMANDO DESILENCIAR ---
    @app_commands.command(name="desilenciar", description="Quita el castigo a un usuario")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def desilenciar(self, interaction: discord.Interaction, usuario: discord.Member):
        try:
            # Para quitar el timeout, lo ponemos a None
            await usuario.timeout(None)
            await interaction.response.send_message(f"✅ **{usuario.display_name}** ha sido liberado del silencio.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al desilenciar: {e}", ephemeral=True)

    @silenciar.error
    @desilenciar.error
    async def mod_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("🚫 Necesitas permiso de **'Moderar Miembros'** para usar esto.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utilidades(bot))