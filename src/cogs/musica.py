import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import logging
import wavelink
from wavelink.enums import TrackSource
from wavelink import TrackEndEventPayload # <-- ¡IMPORTACIÓN CORREGIDA!

# Configuración de Wavelink para manejar eventos (IMPORTANTE)
class CustomPlayer(wavelink.Player):
    """Clase personalizada para manejar eventos de Wavelink, como la finalización de una pista."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.autoplay = wavelink.AutoPlayMode.disabled

    # Usamos el tipo importado directamente
    async def on_track_end(self, payload: TrackEndEventPayload): 
        """Llamado cuando una pista ha terminado de reproducirse."""
        ctx = self.guild.voice_client.ctx # Asumiendo que has almacenado el cog en el player

        if ctx and ctx.colas.get(self.guild.id):
            # Llama a la lógica de la cola para tocar la siguiente
            await ctx.tocar_siguiente(self.guild.id)
            
        # return await super().on_track_end(payload) # Removed: wavelink.Player does not have on_track_end


class Musica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.colas = {}  # Cola por guild
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0'
        }
        # Almacenar la referencia al cog para usarla en el CustomPlayer
        self.bot.on_wavelink_track_end = self._on_wavelink_track_end
    
    # Manejador de evento que redirige al CustomPlayer si es necesario
    async def _on_wavelink_track_end(self, payload: TrackEndEventPayload): # Usamos el tipo importado directamente
        player: CustomPlayer = payload.player
        if player and player.connected:
            # Si el player es nuestro CustomPlayer, llamamos a su método on_track_end
            if isinstance(player, CustomPlayer):
                player.ctx = self # Pasar la referencia al cog
                await player.on_track_end(payload)


    # --- AUTO-DISCONNECT ---
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # SOLO SI EL CANAL ESTÁ VACÍO
        if member.id != self.bot.user.id and before.channel is not None and after.channel != before.channel:
            # Si el bot estaba en el canal del que se desconectó el miembro
            if member.guild.voice_client and before.channel.id == member.guild.voice_client.channel.id:
                canal_bot = member.guild.voice_client.channel
                humanos = [m for m in canal_bot.members if not m.bot]
                
                if len(humanos) == 0:
                    await asyncio.sleep(15)
                    humanos_ahora = [m for m in canal_bot.members if not m.bot]
                    
                    if len(humanos_ahora) == 0 and member.guild.voice_client:
                        # Asegurar que se limpia la cola
                        self.colas.pop(member.guild.id, None)
                        await member.guild.voice_client.disconnect()
                        logging.info(f"🔌 Desconectado de {member.guild.name} por inactividad.")

    # --- OBTENER PLAYER (CORREGIDO) ---
    async def obtener_player(self, interaction: discord.Interaction) -> CustomPlayer | None:
        """Obtiene el reproductor de Wavelink o lo conecta al canal de voz del usuario."""
        
        # 1. Verificar si el usuario está en un canal de voz
        if not interaction.user.voice or not interaction.user.voice.channel:
            # Usar followup porque la interacción ya fue diferida al inicio del comando /musica
            await interaction.followup.send("❌ ¡Debes estar en un canal de voz para usar este comando!", ephemeral=True)
            return None

        # 2. Intentar obtener el reproductor existente (voice_client)
        player: CustomPlayer = interaction.guild.voice_client

        # 3. Si no hay reproductor conectado, conecta el bot
        if not player:
            try:
                # Conexión moderna: usa el método connect() del canal de voz, usando CustomPlayer
                player = await interaction.user.voice.channel.connect(cls=CustomPlayer)
            except Exception as e:
                logging.error(f"❌ Error al conectar al canal de voz: {e}")
                await interaction.followup.send("❌ No pude conectarme al canal de voz. Asegúrate de que el nodo Lavalink esté activo.", ephemeral=True)
                return None
        
        # 4. Asegúrate de que el reproductor está en el mismo canal que el usuario
        if player.channel.id != interaction.user.voice.channel.id:
            await interaction.followup.send("❌ El bot ya está reproduciendo música en otro canal.", ephemeral=True)
            return None

        return player

    # --- REPRODUCIR SIGUIENTE (CORREGIDO FINAL) ---
    async def tocar_siguiente(self, guild_id: int):
        """Reproduce la siguiente canción en la cola."""
        if guild_id not in self.colas or len(self.colas[guild_id]) == 0:
            return

        cancion = self.colas[guild_id].pop(0)
        
        # Obtener el reproductor usando el voice_client del gremio
        player: CustomPlayer = self.bot.get_guild(guild_id).voice_client
        
        if not player or not player.connected:
            return

        # 🛑 CORRECCIÓN APLICADA: Usar wavelink.Track.search y especificar la fuente
        tracks = await wavelink.Playable.search(cancion['titulo'], source=TrackSource.YouTube)
        if not tracks:
            logging.warning(f"⚠️ No se encontró pista para: {cancion['titulo']}")
            # Intenta tocar la siguiente si no se encuentra
            await self.tocar_siguiente(guild_id)
            return

        track = tracks[0] # Usar el primer resultado
        
        # En wavelink v3, play no necesita el nodo, solo el track
        await player.play(track)
        logging.info(f"🎵 Reproduciendo: {track.title}")

    # --- COMANDO /MUSICA (AJUSTADO) ---
    @app_commands.command(name="musica", description="Añade una canción (YouTube o Nombre)")
    async def musica(self, interaction: discord.Interaction, busqueda: str):

        # 1. DIFERIR INMEDIATAMENTE 
        await interaction.response.defer() 

        # 2. Lógica de conexión/obtención del player (AHORA es seguro tardar)
        player = await self.obtener_player(interaction)

        if player is None:
            # obtener_player ya envió el mensaje de error usando followup.
            return

        # Usamos Wavelink para buscar, ya que está conectado
        try:
            # Usa la sintaxis correcta (ya estaba bien aquí)
            tracks = await wavelink.Playable.search(busqueda, source=TrackSource.YouTube)
            if not tracks:
                await interaction.followup.send("❌ No se encontró ninguna canción con ese nombre o URL.", ephemeral=True)
                return

            track = tracks[0]
            
            titulo = track.title
            thumbnail = track.artwork

            cancion = {'titulo': titulo, 'thumbnail': thumbnail, 'usuario': interaction.user.display_name}
            guild_id = interaction.guild.id
            self.colas.setdefault(guild_id, []).append(cancion)

            # Verifica si el reproductor está inactivo (si is_playing es False y no está pausado)
            if not player.playing and not player.paused:
                await self.tocar_siguiente(guild_id)
                # El mensaje de reproducción inicial se envía después de tocar_siguiente
                title_msg = "🎵 Reproduciendo ahora"
                color_code = 0x1db954
            else:
                title_msg = "📝 Añadida a la cola"
                color_code = 0xf1c40f
            
            embed = discord.Embed(
                title=title_msg,
                description=f"**{titulo}**",
                color=color_code
            )
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logging.error(f"❌ Error en comando /musica: {e}")
            await interaction.followup.send(f"❌ Error interno al buscar la música: {e}")


    # --- COMANDOS AUXILIARES (CORREGIDOS) ---
    
    def _get_player(self, guild_id: int) -> CustomPlayer | None:
        """Helper para obtener el player de Wavelink v3."""
        guild = self.bot.get_guild(guild_id)
        return guild.voice_client if guild and guild.voice_client else None


    @app_commands.command(name="saltar", description="Salta a la siguiente canción")
    async def saltar(self, interaction: discord.Interaction):
        player = self._get_player(interaction.guild.id)
        
        if player and player.playing:
            # En wavelink v3, usamos stop() para finalizar la pista actual y activar el evento on_track_end
            await player.stop() 
            await interaction.response.send_message("⏭️ **Saltada!**")
        else:
            await interaction.response.send_message("❌ No hay nada sonando.", ephemeral=True)


    @app_commands.command(name="pausar", description="Pausa la música")
    async def pausar(self, interaction: discord.Interaction):
        player = self._get_player(interaction.guild.id)
        
        if player and player.playing and not player.paused:
            await player.pause()
            await interaction.response.send_message("⏸️ Pausado.")
        else:
            await interaction.response.send_message("❌ No hay nada sonando o ya está pausado.", ephemeral=True)


    @app_commands.command(name="continuar", description="Reanuda la música")
    async def continuar(self, interaction: discord.Interaction):
        player = self._get_player(interaction.guild.id)
        
        if player and player.paused:
            await player.resume()
            await interaction.response.send_message("▶️ Reanudado.")
        else:
            await interaction.response.send_message("❌ No está pausado.", ephemeral=True)


    @app_commands.command(name="salir", description="Saca al bot del canal y borra la cola")
    async def salir(self, interaction: discord.Interaction):
        player = self._get_player(interaction.guild.id)
        
        if player and player.connected:
            # Limpiar la cola y desconectar
            self.colas.pop(interaction.guild.id, None)
            await interaction.response.send_message("👋 **¡Nos vemos!**")
            await player.disconnect()
        else:
            await interaction.response.send_message("❌ No estaba en ningún canal.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Musica(bot))