import os
from datetime import datetime, timedelta, timezone
from . import config


def _generate_with_edge_tts(text: str, output_path: str, voice: str, rate: str) -> bool:
    try:
        import asyncio
        import edge_tts

        async def _run():
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(output_path)

        asyncio.run(_run())
        return True
    except Exception as e:
        print(f"  [WARN] edge-tts失敗: {e}")
        return False


def _generate_with_gtts(text: str, output_path: str) -> bool:
    try:
        from gtts import gTTS
        tts = gTTS(text, lang="ja")
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"  [WARN] gTTS失敗: {e}")
        return False


def generate_audio(script: str, output_dir: str | None = None) -> str:
    jst = timezone(timedelta(hours=9))
    timestamp = datetime.now(jst).strftime("%Y%m%d_%H%M%S")
    out_dir = output_dir or config.OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    script_path = os.path.join(out_dir, f"news_digest_{timestamp}.txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"📝 原稿を保存: {script_path}")

    audio_path = os.path.join(out_dir, f"news_digest_{timestamp}.mp3")

    # 1. edge-tts (highest quality, Japanese support)
    print("🎙️ 音声生成中 (edge-tts)...")
    if _generate_with_edge_tts(script, audio_path, config.TTS_VOICE_JA, "-5%"):
        print(f"🔊 音声ファイルを保存: {audio_path}")
        return audio_path

    # 2. gTTS fallback
    print("🎙️ 音声生成中 (gTTS)...")
    if _generate_with_gtts(script, audio_path):
        print(f"🔊 音声ファイルを保存: {audio_path}")
        return audio_path

    # 3. Script-only fallback
    print("⚠️  TTSエンジンが利用できません。原稿ファイルのみ生成しました。")
    print("   ローカル環境で以下を実行して音声を生成してください:")
    print(f"   pip install edge-tts && python -m edge_tts --voice ja-JP-NanamiNeural --rate=-5% -f {script_path} --write-media {audio_path}")
    return script_path
