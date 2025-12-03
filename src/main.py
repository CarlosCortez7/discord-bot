import discord
import os
import logging
from discord.ext import commands
from dotenv import load_dotenv

# --- CONFIGURACIÓN ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True

class HerxinBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        extensions = [
            'src.cogs.auditoria',
            'src.cogs.tareas',
            'src.cogs.utilidades',
            'src.cogs.bienvenida',
            'src.cogs.musica',
            'src.cogs.temporales',
            'src.cogs.ayuda',
            'src.cogs.juegos',
            # 'src.cogs.ayuda' # Descomenta si usas el de ayuda
        ]

        for ext in extensions:
            try:
                await self.load_extension(ext)
                logging.info(f"⚙️  Módulo cargado: {ext}")
            except Exception as e:
                logging.error(f"❌ Error cargando {ext}: {e}")

    async def on_ready(self):
        logging.info(f'✅ Logueado como: {self.user}')
        await self.change_presence(activity=discord.Game(name="version v1.0"))

bot = HerxinBot()

# --- COMANDO DE SYNC MEJORADO ---
@bot.command()
async def sync(ctx, opcion: str = None):
    """
    !sync        -> Sincroniza solo este servidor (Rápido)
    !sync global -> Borra comandos viejos de la nube (Lento pero efectivo)
    """
    if opcion == "global":
        msg = await ctx.send("🌍 **Sincronizando Globalmente...**\nEsto borrará los comandos viejos (`/add`) de la nube.\nPuede tardar unos segundos...")
        try:
            # Esto actualiza la lista global de Discord con lo que tienes AHORA
            synced = await bot.tree.sync()
            await msg.edit(content=f"✅ **¡Limpieza Global completada!**\nComandos actuales: {len(synced)}.\n\n*Nota: Si aún ves el comando viejo, presiona Ctrl + R en Discord.*")
            logging.info(f"Sync Global: {len(synced)} comandos.")
        except Exception as e:
            await msg.edit(content=f"❌ Error: {e}")
    else:
        msg = await ctx.send(f"🏠 Sincronizando solo en **{ctx.guild.name}**...")
        try:
            bot.tree.copy_global_to(guild=ctx.guild)
            synced = await bot.tree.sync(guild=ctx.guild)
            await msg.edit(content=f"✅ **¡Sincronización Local lista!** {len(synced)} comandos activos.")
        except Exception as e:
            await msg.edit(content=f"❌ Error: {e}")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)