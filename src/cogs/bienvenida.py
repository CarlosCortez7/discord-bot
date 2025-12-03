import discord
from discord.ext import commands
import logging
import random

class Bienvenida(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Nombres posibles del canal de bienvenida (puedes editar esto)
        self.target_channels = ["👋・recepción", "recepción", "bienvenida", "general"]
        # GIFs random de Minecraft para darle vida
        self.gifs = [
            "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExN3k5NzZwMHVva2dzaHNmZGkxeGM5eGU4cGpuNGNtaTZoMzdsYXZwYSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/IzQts6KDjZqTMkWAfe/giphy.gif"
        ]

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = None

        # Busca el primer canal que coincida con la lista de nombres
        for name in self.target_channels:
            channel = discord.utils.get(guild.text_channels, name=name)
            if channel:
                break
        
        if not channel:
             logging.warning(f"⚠️ No encontré un canal de bienvenida para saludar a {member.name}.")
             return

        # Crear el Embed
        embed = discord.Embed(
            title=f"¡Un nuevo sobreviviente ha llegado! 🌲",
            description=f"Hola {member.mention}, bienvenido al refugio **{guild.name}**.\n\n"
                        f"👉 **Espera aquí a que un Admin te verifique.**",
            color=0x57F287 # Verde discord
        )

        # Poner el avatar del usuario en pequeño
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        # Poner un GIF grande abajo
        embed.set_image(url=random.choice(self.gifs))

        # Footer con el contador de miembros
        embed.set_footer(text=f"Contigo somos {guild.member_count} miembros")

        try:
            await channel.send(embed=embed)
            logging.info(f"👋 Bienvenida enviada para {member.name} en #{channel.name}.")
        except discord.Forbidden:
             logging.error(f"❌ Permiso denegado para enviar bienvenida en #{channel.name}.")

async def setup(bot):
    await bot.add_cog(Bienvenida(bot))