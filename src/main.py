
class HerxinBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.cog_load_errors = []

    async def setup_hook(self):
        # --- CARGAR COGS ---
        # Lista de cogs (sin prefijo)
        cogs_list = [
            'auditoria',
            'tareas',
            'utilidades',
            'bienvenida',
            'musica',
            'temporales',
            'ayuda',
            'juegos',
        ]

        for ext in cogs_list:
            loaded = False
            error_msg = ""
            # Intentar cargar con prefijo 'cogs.' (común si se ejecuta desde src/ o script directo)
            try:
                await self.load_extension(f"cogs.{ext}")
                logging.info(f"⚙️  Módulo cargado: cogs.{ext}")
                loaded = True
            except Exception as e:
                error_msg = str(e)

            # Si falló, intentar con 'src.cogs.' (común si se ejecuta desde root como módulo)
            if not loaded:
                try:
                    await self.load_extension(f"src.cogs.{ext}")
                    logging.info(f"⚙️  Módulo cargado: src.cogs.{ext}")
                    loaded = True
                except Exception as e:
                    full_error = f"❌ Error cargando {ext}: {e} | Previo: {error_msg}"
                    logging.error(full_error)
                    self.cog_load_errors.append(f"**{ext}**: {e}")

        # --- SYNC AUTOMÁTICO DE SLASH COMMANDS ---
        try:
            synced = await self.tree.sync()
            logging.info(f"🔄 Sync inicial completado: {len(synced)} comandos.")
        except Exception as e:
            logging.error(f"❌ Error en sync inicial: {e}")

    async def on_ready(self):
        logging.info(f'✅ Logueado como: {self.user}')
        logging.info(f'📂 Directorio de trabajo actual: {os.getcwd()}')
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

# --- COMANDO DE DIAGNÓSTICO ---
@bot.command()
async def debug(ctx):
    """Muestra el estado de los módulos y errores de carga."""
    loaded = list(bot.extensions.keys())
    
    msg = f"📂 **Directorio:** `{os.getcwd()}`\n"
    msg += f"🧩 **Cogs cargados ({len(loaded)}):**\n`{', '.join(loaded)}`\n\n"
    
    if bot.cog_load_errors:
        msg += "⚠️ **Errores de carga:**\n"
        for err in bot.cog_load_errors:
            msg += f"- {err}\n"
    else:
        msg += "✅ **No hubo errores de carga.**"
        
    await ctx.send(msg)

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