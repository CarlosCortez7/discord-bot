import discord
from discord.ext import commands
import logging

class Temporales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 🔴 IMPORTANTE: PEGA AQUÍ LA ID DEL CANAL "➕ Crear Sala"
        self.channel_hub_id = 1445588861089615984

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # 1. LOGICA DE CREACIÓN (Cuando alguien entra al Hub)
        if after.channel and after.channel.id == self.channel_hub_id:
            guild = member.guild
            
            # Obtenemos la categoría para crear la sala ahí mismo
            categoria = after.channel.category
            
            # Creamos el canal con el nombre del usuario
            # (Overwrites permite que el usuario tenga permisos de admin en su sala si quieres)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=True),
                member: discord.PermissionOverwrite(connect=True, move_members=True, manage_channels=True)
            }
            
            nombre_sala = f"Sala de {member.display_name}"
            
            try:
                # Crear canal
                nuevo_canal = await guild.create_voice_channel(
                    name=nombre_sala, 
                    category=categoria,
                    overwrites=overwrites
                )
                
                # Mover al usuario a su nueva sala
                await member.move_to(nuevo_canal)
                logging.info(f"✅ Sala temporal creada: {nombre_sala}")
                
            except Exception as e:
                logging.error(f"❌ Error creando sala temporal: {e}")

        # 2. LOGICA DE DESTRUCCIÓN (Cuando alguien sale de CUALQUIER canal)
        if before.channel:
            # Verificamos si el canal que se dejó está vacío ahora
            if len(before.channel.members) == 0:
                
                # REGLAS PARA BORRAR:
                # A. El canal debe estar en la misma categoría que el Hub (para no borrar canales de otros lados)
                # B. El canal NO debe ser el Hub ("Crear Sala")
                
                hub_channel = member.guild.get_channel(self.channel_hub_id)
                
                # Si por alguna razón no encuentra el hub, abortamos para seguridad
                if not hub_channel: 
                    return

                es_misma_categoria = before.channel.category_id == hub_channel.category_id
                es_el_hub = before.channel.id == self.channel_hub_id
                
                if es_misma_categoria and not es_el_hub:
                    try:
                        await before.channel.delete()
                        logging.info(f"🗑️ Sala vacía eliminada: {before.channel.name}")
                    except Exception as e:
                        logging.error(f"❌ Error borrando sala: {e}")

async def setup(bot):
    await bot.add_cog(Temporales(bot))