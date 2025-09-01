import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs de configuração
TICKET_CATEGORY_ID = 1411488664260706394 # ID da categoria onde os tickets serão criados
LOG_CHANNEL_ID = 1410799060759216172      # ID do canal de logs
SUPPORT_ROLES = [1409274874962120778]  # IDs dos cargos de suporte


# ===== VIEW DO BOTÃO PRINCIPAL =====
class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # Verifica se já existe um ticket para este usuário
        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{user.name}".lower())
        if existing_channel:
            await interaction.response.send_message(f"Você já tem um ticket aberto: {existing_channel.mention}", ephemeral=True)
            return

        # Categoria dos tickets
        category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
        if category is None:
            await interaction.response.send_message("⚠ Categoria de tickets não encontrada!", ephemeral=True)
            return

        # Permissões
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Adiciona cargos de suporte
        for role_id in SUPPORT_ROLES:
            role = guild.get_role(1410018960962752563)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Cria o canal do ticket
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites,
            reason=f"Ticket criado por {user}"
        )

        # Embed dentro do ticket
        await ticket_channel.send(f"<@&1409274874962120778>")
        ticket_embed = discord.Embed(
            title="🎫 Ticket Aberto",
            description=f"Olá {user.mention}!\nNossa equipe entrará em contato em breve.\nClique no botão abaixo para fechar este ticket quando terminar.",
            color=discord.Color.green()
        )
        ticket_embed.set_footer(text=f"Ticket de {user.name}", icon_url=user.display_avatar.url)

        # Botão de fechar
        close_view = View(timeout=None)
        close_button = Button(label="Fechar Ticket", style=discord.ButtonStyle.red)

        async def close_callback(interaction_close: discord.Interaction):
            if interaction_close.user != user and not any(role.id in SUPPORT_ROLES for role in interaction_close.user.roles):
                await interaction_close.response.send_message("voce nao tem permissao para fechar este ticket!", ephemeral=False)
                return

            await interaction_close.response.send_message("<a:straws_loading:1411489481235894322> | seu ticket sera fechado em 5 segundos.", ephemeral=False)
            await asyncio.sleep(5)

            # Log do fechamento
            log_channel = guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title="📕 Ticket Fechado",
                    description=f"O ticket {ticket_channel.name} foi fechado por {interaction_close.user.mention}",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="Usuário", value=user.mention, inline=True)
                log_embed.add_field(name="Fechado por", value=interaction_close.user.mention, inline=True)
                await log_channel.send(embed=log_embed)

            await ticket_channel.delete()

        close_button.callback = close_callback
        close_view.add_item(close_button)

        await ticket_channel.send(embed=ticket_embed, view=close_view)
        await interaction.response.send_message(f"✅ Seu ticket foi criado: {ticket_channel.mention}", ephemeral=True)


# ===== SLASH COMMAND PARA CRIAR O PAINEL =====
@bot.tree.command(name="ticket", description="Cria o painel de abertura de tickets")
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Sistema de Tickets",
        description="Clique no botão abaixo para abrir um ticket com a equipe de suporte!",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Ticket System V2")
    view = TicketPanelView()
    await interaction.response.send_message(embed=embed, view=view)


# ===== EVENTO ON_READY PARA SINCRONIZAR =====
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Comandos slash sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


bot.run("")