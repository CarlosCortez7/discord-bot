import discord
from discord.ext import commands
import logging

class Auditoria(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- EVENTO: MENSAJE BORRADO ---
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Ignorar mensajes de bots para no hacer spam
        if message.author.bot:
            return

        # Buscamos el canal de logs
        log_channel = discord.utils.get(message.guild.channels, name="logs")
        
        if log_channel:
            embed = discord.Embed(title="🗑️ Mensaje Eliminado", color=0xe74c3c)
            embed.add_field(name="Autor", value=message.author.mention, inline=True)
            embed.add_field(name="Canal", value=message.channel.mention, inline=True)
            # Si el mensaje tenía texto, lo mostramos. Si era solo foto, avisamos.
            contenido = message.content if message.content else "*[Solo imagen/archivo]*"
            embed.add_field(name="Contenido", value=f"```{contenido}```", inline=False)
            embed.set_footer(text=f"ID: {message.author.id}")
            
            await log_channel.send(embed=embed)

    # --- EVENTO: MENSAJE EDITADO ---
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # Ignorar si es bot o si el contenido no cambió (ej: Discord a veces actualiza embeds)
        if before.author.bot or before.content == after.content:
            return

        log_channel = discord.utils.get(before.guild.channels, name="logs")

        if log_channel:
            embed = discord.Embed(title="✏️ Mensaje Editado", color=0xf1c40f)
            embed.add_field(name="Autor", value=before.author.mention, inline=False)
            embed.add_field(name="Canal", value=before.channel.mention, inline=False)
            embed.add_field(name="Antes", value=f"```{before.content}```", inline=False)
            embed.add_field(name="Después", value=f"```{after.content}```", inline=False)
            # Link para ir directo al mensaje editado
            embed.add_field(name="Ir al mensaje", value=f"[Click Aquí]({after.jump_url})", inline=False)
            
            await log_channel.send(embed=embed)

# Función de configuración obligatoria para cargar el Cog
async def setup(bot):
    await bot.add_cog(Auditoria(bot))