import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import logging

class Musica(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.colas = {} 
        
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0'
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

    # --- DETECTOR DE SOLEDAD (AUTO-DISCONNECT) ---
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.guild.voice_client:
            return

        canal_bot = member.guild.voice_client.channel

        if before.channel == canal_bot:
            humanos = [m for m in canal_bot.members if not m.bot]

            if len(humanos) == 0:
                await asyncio.sleep(15)
                humanos_ahora = [m for m in canal_bot.members if not m.bot]
                if len(humanos_ahora) == 0 and member.guild.voice_client:
                    if member.guild.id in self.colas:
                        self.colas[member.guild.id] = []
                    await member.guild.voice_client.disconnect()
                    logging.info(f"🔌 Desconectado de {member.guild.name} por inactividad.")

    # --- MOTOR DE REPRODUCCIÓN ---
    def tocar_siguiente(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        if guild_id in self.colas and len(self.colas[guild_id]) > 0:
            cancion = self.colas[guild_id].pop(0)
            url_audio = cancion['url']
            
            vc = interaction.guild.voice_client
            
            if not vc:
                return

            try:
                source = discord.FFmpegPCMAudio(url_audio, **self.ffmpeg_options)
                vc.play(source, after=lambda e: self.tocar_siguiente(interaction))
            except Exception as e:
                print(f"Error reproduciendo: {e}")
                self.tocar_siguiente(interaction)
        else:
            pass

    async def conectar_voz(self, interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ ¡No estás en un canal de voz!", ephemeral=True)
            return None
        
        canal = interaction.user.voice.channel
        if not interaction.guild.voice_client:
            await canal.connect()
        elif interaction.guild.voice_client.channel != canal:
            await interaction.guild.voice_client.move_to(canal)
            
        return interaction.guild.voice_client

    # --- COMANDOS ---

    @app_commands.command(name="musica", description="Añade una canción (YouTube o Nombre)")
    async def musica(self, interaction: discord.Interaction, busqueda: str):
        vc = await self.conectar_voz(interaction)
        if not vc:
            return

        await interaction.response.defer()

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(busqueda, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                
                url_audio = info['url']
                titulo = info.get('title', 'Canción desconocida')
                thumbnail = info.get('thumbnail', None)

            cancion = {
                'titulo': titulo,
                'url': url_audio,
                'thumbnail': thumbnail,
                'usuario': interaction.user.display_name
            }

            guild_id = interaction.guild.id
            if guild_id not in self.colas:
                self.colas[guild_id] = []

            if vc.is_playing() or vc.is_paused():
                self.colas[guild_id].append(cancion)
                embed = discord.Embed(title="📝 Añadida a la cola", description=f"**{titulo}**", color=0xf1c40f)
                embed.set_footer(text=f"Posición: #{len(self.colas[guild_id])}")
                await interaction.followup.send(embed=embed)
            
            else:
                self.colas[guild_id].append(cancion)
                self.tocar_siguiente(interaction)
                embed = discord.Embed(title="🎵 Reproduciendo ahora", description=f"**{titulo}**", color=0x1db954)
                if thumbnail:
                    embed.set_thumbnail(url=thumbnail)
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error al buscar: {e}")

    @app_commands.command(name="saltar", description="Salta a la siguiente canción")
    async def saltar(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop() 
            await interaction.response.send_message("⏭️ **Saltada!**", ephemeral=False)
        else:
            await interaction.response.send_message("❌ No hay nada sonando.", ephemeral=True)

    @app_commands.command(name="lista_musica", description="Ver la cola de reproducción")
    async def lista_musica(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.colas or not self.colas[guild_id]:
            await interaction.response.send_message("📂 La cola está vacía.", ephemeral=True)
            return

        texto = ""
        # Mostramos hasta 15 canciones
        for i, cancion in enumerate(self.colas[guild_id][:15], 1):
            texto += f"**{i}.** {cancion['titulo']} *(por {cancion['usuario']})*\n"
        
        if len(self.colas[guild_id]) > 15:
            texto += f"\n*...y {len(self.colas[guild_id]) - 15} más.*"

        embed = discord.Embed(title="📜 Cola de Música", description=texto, color=0x3498db)
        embed.set_footer(text="Usa /eliminar [numero] para borrar una canción.")
        await interaction.response.send_message(embed=embed)

    # --- COMANDO NUEVO: REMOVER ---
    @app_commands.command(name="eliminar", description="Elimina una canción específica de la cola")
    @app_commands.describe(numero="El número de la canción (Ver /lista_musica)")
    async def eliminar(self, interaction: discord.Interaction, numero: int):
        guild_id = interaction.guild.id
        
        # Verificar si hay cola
        if guild_id not in self.colas or not self.colas[guild_id]:
            await interaction.response.send_message("📂 La cola ya está vacía.", ephemeral=True)
            return

        # Ajustamos el índice (Usuario dice 1, Python entiende 0)
        indice = numero - 1

        # Verificamos que el número sea válido
        if 0 <= indice < len(self.colas[guild_id]):
            cancion_borrada = self.colas[guild_id].pop(indice)
            await interaction.response.send_message(f"🗑️ Eliminada de la cola: **{cancion_borrada['titulo']}**")
        else:
            await interaction.response.send_message(f"❌ Número inválido. La cola tiene {len(self.colas[guild_id])} canciones.", ephemeral=True)

    @app_commands.command(name="pausar", description="Pausa la música")
    async def pausar(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Pausado.")
        else:
            await interaction.response.send_message("❌ No hay nada sonando.", ephemeral=True)

    @app_commands.command(name="continuar", description="Reanuda la música")
    async def continuar(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Reanudado.")
        else:
            await interaction.response.send_message("❌ No está pausado.", ephemeral=True)

    @app_commands.command(name="salir", description="Saca al bot del canal y borra la cola")
    async def salir(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in self.colas:
            self.colas[guild_id] = [] 
            
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            await vc.disconnect()
            await interaction.response.send_message("👋 **¡Nos vemos!**")
        else:
            await interaction.response.send_message("❌ No estaba en ningún canal.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Musica(bot))