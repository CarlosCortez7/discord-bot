import discord
from discord.ext import commands
from discord import app_commands
from discord import ui

# --- CLASE DEL MENÚ INTERACTIVO ---
class MenuSeleccion(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="👤 Comandos de Usuario", 
                emoji="📱", 
                description="Música, Tareas, juegos y utilidades"
            ),
            discord.SelectOption(
                label="🛡️ Zona Administrativa", 
                emoji="🔐", 
                description="Moderación y Sistemas Automáticos"
            )
        ]
        super().__init__(placeholder="📂 Selecciona una categoría...", max_values=1, min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        opcion = self.values[0]
        
        embed = discord.Embed(title=f"{opcion}", color=0x3498db)

        if opcion == "👤 Comandos de Usuario":
            embed.description = """
            **🎵 MÚSICA Y DJ**
            `/musica [nombre/link]` - Pone una canción (YouTube).
            `/saltar` - Salta a la siguiente canción.
            `/pausar` y `/continuar` - Controla la reproducción.
            `/lista_musica` - Muestra la cola de espera.    
            `/eliminar [numero]` - Elimina una canción de la cola.
            `/salir` - Saca al bot del canal y borra la cola.

            **📝 TAREAS Y ESTUDIO**
            `/tarea` - Abre el formulario para crear recordatorios.
            `/lista` - Muestra tus tareas pendientes.
            `/done [id]` - Marca una tarea como completada.

            **🛠️ UTILIDADES**
            `/perfil` - Muestra tu ficha técnica.
            `/perfil [usuario]` - Muestra la ficha técnica de alguien.
            `/encuesta` - Crea una votación automática.

            **📝 JUEGOS**
            `/decir [mensaje]` - Haz que el bot hable por ti (Anónimo).
            `/decir [mensaje] [usuario]` - Haz que el bot hable por ti (Anónimo).
            `/ship [usuario1] [usuario2]` - Calcula la compatibilidad entre dos personas.
            """
        
        elif opcion == "🛡️ Zona Administrativa":
            embed.description = """
            **👮 MODERACIÓN**
            `/limpiar [cantidad]` - Borra mensajes recientes (Requiere permisos).
            `/anuncio [titulo] [mensaje]` - Envia un anuncio.
            `/silenciar [usuario] [tiempo] [razón]` - Silencia a un usuario temporalmente.
            `/desilenciar [usuario]` - Quitar el castigo a un usuario.
            `/limpiar [cantidad] [usuario]` - Borra mensajes recientes (Requiere permisos).
            `/fake [usuario] [mensaje]` - Envía un mensaje haciéndote pasar por otro usuario (Solo Admins).
            
            **⚙️ MANTENIMIENTO (Solo Owner)**
            `!sync` - Sincroniza los comandos en este servidor.
            `!sync global` - Limpieza profunda de comandos en la nube.

            **🤖 SISTEMAS AUTOMÁTICOS (Activos)**
            • **Auditoría:** Reporta mensajes borrados/editados en `#logs`.
            • **Bienvenida:** Saluda con tarjeta visual a los nuevos.
            • **Salas Temporales:** Crea canales de voz dinámicos en '➕ Crear Sala'.
            • **Auto-Desconexión:** El bot se sale del chat de voz si se queda solo.
            """

        await interaction.response.edit_message(embed=embed, view=VistaAyuda())

# --- CLASE DE LA VISTA (Contenedor) ---
class VistaAyuda(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(MenuSeleccion())

# --- COG PRINCIPAL ---
class Ayuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ayuda", description="Muestra la lista de comandos actualizada")
    async def ayuda(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Centro de Ayuda Herxin-Bot", 
            description="Aquí tienes la documentación de la versión 1.0.\nSelecciona tu rol abajo:", 
            color=0x5865F2
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await interaction.response.send_message(embed=embed, view=VistaAyuda(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ayuda(bot))