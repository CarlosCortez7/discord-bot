import discord
import os
import logging
from discord.ext import commands
from dotenv import load_dotenv
import wavelink  # <-- IMPORTANTE

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
        # --- CARGAR COGS ---
        extensions = [
            'src.cogs.auditoria',
            'src.cogs.tareas',
            'src.cogs.utilidades',
            'src.cogs.bienvenida',
            'src.cogs.musica',
            'src.cogs.temporales',
            'src.cogs.ayuda',
            'src.cogs.juegos',
        ]

        for ext in extensions:
            try:
                await self.load_extension(ext)
                logging.info(f"⚙️  Módulo cargado: {ext}")
            except Exception as e:
                logging.error(f"❌ Error cargando {ext}: {e}")

        # --- SYNC AUTOMÁTICO DE SLASH COMMANDS ---
        try:
            synced = await self.tree.sync()
            logging.info(f"🔄 Sync inicial completado: {len(synced)} comandos.")
        except Exception as e:
            logging.error(f"❌ Error en sync inicial: {e}")

    async def on_ready(self):
        logging.info(f'✅ Logueado como: {self.user}')
        await self.change_presence(activity=discord.Game(name="version v1.0"))

        # --- CONECTAR NODO PÚBLICO DE LAVALINK ---
        try:
            node = wavelink.Node(
                uri='http://lavalink.serenetia.com:80',
                password='https://dsc.gg/ajidevserver'
            )
            await wavelink.Pool.connect(client=self, nodes=[node])
            logging.info("🔊 Nodo Lavalink conectado")
        except Exception as e:
            logging.error(f"❌ Error conectando al nodo Lavalink: {e}")

bot = HerxinBot()

# --- COMANDO DE SYNC MANUAL ---
@bot.command()
async def sync(ctx, opcion: str = None):
    if opcion == "global":
        msg = await ctx.send("🌍 **Sincronizando Globalmente...**")
        try:
            synced = await bot.tree.sync()
            await msg.edit(content=f"✅ **Sync Global completado:** {len(synced)} comandos.")
        except Exception as e:
            await msg.edit(content=f"❌ Error: {e}")
    else:
        msg = await ctx.send(f"🏠 Sincronizando solo en **{ctx.guild.name}**...")
        try:
            bot.tree.copy_global_to(guild=ctx.guild)
            synced = await bot.tree.sync(guild=ctx.guild)
            await msg.edit(content=f"✅ **Sync Local completado:** {len(synced)} comandos.")
        except Exception as e:
            await msg.edit(content=f"❌ Error: {e}")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERROR: No se encontró DISCORD_TOKEN en el archivo .env")