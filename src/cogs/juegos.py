import discord
import random
from datetime import datetime
from discord.ext import commands
from discord import app_commands

class Juegos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- COMANDO: TITIRITERO (/DECIR) ---
    @app_commands.command(name="decir", description="Haz que el bot hable por ti (Anónimo)")
    @app_commands.describe(mensaje="Lo que dirá el bot", usuario="(Opcional) ¿A quién etiquetar?")
    async def decir(self, interaction: discord.Interaction, mensaje: str, usuario: discord.Member = None):
        texto_final = mensaje
        if usuario:
            texto_final = f"{usuario.mention} {mensaje}"

        await interaction.channel.send(texto_final)
        await interaction.response.send_message("✅ Mensaje enviado.", ephemeral=True)

    # --- COMANDO: SHIPPEO (CALCULADORA DE AMOR) ---
    @app_commands.command(name="ship", description="Calcula el porcentaje de amor entre dos personas")
    @app_commands.describe(usuario1="El primer tortolito", usuario2="El segundo tortolito")
    async def ship(self, interaction: discord.Interaction, usuario1: discord.Member, usuario2: discord.Member):
        # 1. Generar una semilla única basada en el día y los IDs
        # Esto hace que el resultado sea EL MISMO durante todo el día para esa pareja.
        fecha_hoy = datetime.now().strftime("%Y%m%d")
        # Ordenamos los IDs para que ship(Juan, Pedro) sea igual a ship(Pedro, Juan)
        ids = sorted([usuario1.id, usuario2.id])
        semilla = int(fecha_hoy) + ids[0] + ids[1]
        
        # Iniciamos el generador aleatorio con esa semilla
        rnd = random.Random(semilla)
        porcentaje = rnd.randint(0, 100)

        # 2. Barra de progreso visual
        bloques = int(porcentaje / 10) # Ej: 50% son 5 bloques
        barra = "🟩" * bloques + "⬛" * (10 - bloques)

        # 3. Mensaje y Color según el resultado
        if porcentaje <= 20:
            titulo = "💔 Incompatible"
            desc = "Ni lo intenten... terminará mal."
            color = 0x000000 # Negro
            gif = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExeXQ0YnNldjFveHFtejdrNms1ZjRnZm80d2kzY2QwM3kyY2syMHJxbSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/TL7agkazqnyec/giphy.gif"
        elif porcentaje <= 50:
            titulo = "😐 Amigos y ya"
            desc = "Mejor quédense en la friendzone."
            color = 0xf1c40f # Amarillo
            gif = "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExdTMzM24ydWVzejk4ejVqbDVlbjdvOTVtb3RqbjdwaTdhdXVqamNldiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xHwK0JDK5jPwY/giphy.gif"
        elif porcentaje <= 80:
            titulo = "💖 Hay futuro"
            desc = "Con un poco de esfuerzo, puede funcionar."
            color = 0xe91e63 # Rosa
            gif = "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdzF3cWl2bWt5emY4bnB4ZTY5Z253NDhybnMxbjd3YTU1am1vNHIyNyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/CjToMcHtgrKzCjatVL/giphy.gif"
        else:
            titulo = "🔥 ¡BODA!"
            desc = "¡Son el uno para el otro! ¿Para cuándo los anillos?"
            color = 0xff0000 # Rojo Intenso
            gif = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYXowbnplOGh3b3Q2eDFvcmM0Ym5lM210NXVpY2h1OXpsZWUwZ2c5dCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/wG1i2KJyB3zlC/giphy.gif"

        # 4. Crear el Embed
        embed = discord.Embed(title=f"💘 Calculadora de Amor", description=f"{usuario1.mention} **x** {usuario2.mention}", color=color)
        embed.add_field(name="Compatibilidad", value=f"**{porcentaje}%**\n`{barra}`", inline=False)
        embed.add_field(name=f"{titulo}", value=desc, inline=False)
        
        if gif:
            embed.set_thumbnail(url=gif)

        await interaction.response.send_message(embed=embed)

    # --- COMANDO: IMPOSTOR PERFECTO (/FAKE) ---
    @app_commands.command(name="fake", description="Envía un mensaje haciéndote pasar por otro usuario (Solo Admins)")
    @app_commands.describe(usuario="¿A quién quieres suplantar?", mensaje="Lo que dirá")
    @app_commands.checks.has_permissions(administrator=True) # Restricción de seguridad
    async def fake(self, interaction: discord.Interaction, usuario: discord.Member, mensaje: str):
        # Diferimos la respuesta para que no se vea el "Bot está pensando"
        await interaction.response.defer(ephemeral=True)

        try:
            # 1. Crear un Webhook temporal en el canal
            webhook = await interaction.channel.create_webhook(name=usuario.display_name)
            
            # 2. Usar el Webhook para enviar el mensaje con la foto y nombre del usuario
            await webhook.send(
                content=mensaje, 
                username=usuario.display_name, 
                avatar_url=usuario.display_avatar.url
            )
            
            # 3. Borrar el Webhook para no dejar basura
            await webhook.delete()
            
            # 4. Confirmar al admin
            await interaction.followup.send(f"😈 Mensaje fake enviado como {usuario.mention}", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send("❌ No tengo permisos para crear Webhooks (Gestionar Webhooks).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

    # Manejo de error de permisos para /fake
    @fake.error
    async def fake_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("🚫 Este comando es solo para Administradores.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Juegos(bot))