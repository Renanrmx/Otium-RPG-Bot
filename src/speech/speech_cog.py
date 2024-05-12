import os
import asyncio
import logging

import discord
from discord.ext import commands
from speech_recognition import RequestError, UnknownValueError
from speech.sr_sink import SRSink
from speech.assistant import GeminiAssistant


LANGUAGE = os.getenv("LANGUAGE")
COMMAND_PUBLIC_IA = os.getenv("COMMAND_PUBLIC_IA")
COMMAND_PRIVATE_IA = os.getenv("COMMAND_PRIVATE_IA")
COMMAND_DISABLE_IA = os.getenv("COMMAND_DISABLE_IA")

logger = logging.getLogger("speech.speech_cog")


class SpeechCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connections = {}

        self.enabledAi = False
        self.isPrivateAi = False

        self.assistant = GeminiAssistant()

    @discord.command(
        description='Ativa o assistente no canal de voz para transcrição e comandos'
    )
    @discord.command()
    async def otium_start(self, ctx: discord.ApplicationContext):
        voice = ctx.author.voice
        if not voice:
            return await ctx.respond("Não está no canal de voz")

        vc = await voice.channel.connect()
        self.connections.update({ctx.guild.id: vc})

        # The recording takes place in the sink object.
        # SRSink will discard the audio once is transcribed.
        vc.start_recording(SRSink(self.speech_callback_bridge, ctx), self.stop_callback)

        await ctx.respond("Iniciado")

    @discord.command(
        description='Pare a transcrição e comandos no canal de voz'
    )
    @discord.command()
    async def otium_stop(self, ctx: discord.ApplicationContext):
        if ctx.guild.id in self.connections:
            vc = self.connections[ctx.guild.id]
            vc.stop_recording()
            del self.connections[ctx.guild.id]
            await ctx.delete()
        else:
            await ctx.respond("Não foi possível ouvir nesta grupo")

    @discord.command(
        description='Peça algo ao assistente de mestre'
    )
    async def otium_assist(self, ctx, prompt: str):
        try:
            response = self.assistant.send_prompt(prompt)
            await ctx.send(response)
        except:
            await ctx.response.send_message(f"Desculpe, ocorreu um erro.")

    async def stop_callback(self, sink):
        await sink.vc.disconnect()

    def speech_callback_bridge(self, recognizer, audio, ctx, user):
        asyncio.run_coroutine_threadsafe(
            self.speech_callback(recognizer, audio, ctx, user), self.bot.loop
        )

    async def speech_callback(self, recognizer, audio, ctx, userId):
        try:
            text = recognizer.recognize_google(audio, language=LANGUAGE).lower()
        except UnknownValueError:
            logger.debug("Google Speech não conseguiu compreender o audio")
        except RequestError as e:
            logger.exception(
                "Não foi possível requisitar o resultado do serviço Google Speech Recognition",
                exc_info=e,
            )
        else:
            if COMMAND_PUBLIC_IA in text:
                self.enabledAi = True
                self.isPrivateAi = False
                await ctx.send(f"**IA Ativada (Público), fale suas instruções**")

            elif COMMAND_PRIVATE_IA in text:
                self.enabledAi = True
                self.isPrivateAi = True
                await ctx.send(f"**IA Ativada (Privado), fale suas instruções**")

            elif COMMAND_DISABLE_IA in text:
                self.enabledAi = False
                await ctx.send(f"**IA Desativada**")

            if self.enabledAi:
                if self.isPrivateAi:
                    response = self.assistant.send_prompt(text)
                    await ctx.user.send(response)
                else:
                    response = self.assistant.send_prompt(text)
                    await ctx.send(response)
            else:
                await ctx.send(f"<@{userId}>: {text}")


def setup(bot):
    bot.add_cog(SpeechCog(bot))
