import asyncio
import discord
import firebase_admin
from firebase_admin import credentials, firestore, storage

# Firebaseの初期化
cred = credentials.Certificate('')
firebase_admin.initialize_app(cred, {
    'projectId': ''
})

db = firestore.client()
keywords_ref = db.collection('keywords')
bucket = storage.bucket('')

# Discordクライアントの作成
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')

@client.event
async def on_message(message):
    if message.author.bot:
        # メッセージがBotからのものなら何もしない
        return

    if message.content.startswith('!add'):
        # !add コマンドの処理
        print('!add')
        keyword = message.content.split('"')[1].lower()
        await message.channel.send('アップロードする画像を送信してください')

        # 画像が送信されるのを待つ
        def check(m):
            return m.author == message.author and m.attachments

        try:
            img_msg = await client.wait_for('message', timeout=60, check=check)
        except asyncio.TimeoutError:
            await message.channel.send('タイムアウトしました。最初からやり直してください。')
            return

        # 画像をFirebase Storageにアップロード
        attachment = img_msg.attachments[0]
        image_data = await attachment.read()
        blob = bucket.blob(f'{keyword}')
        blob.upload_from_string(image_data, content_type=attachment.content_type)
        image_url = blob.public_url

        # キーワードとimage_urlをFirestoreに登録
        keywords_ref.document(keyword).set({'keyword': keyword, 'imageurl': image_url})
        await message.channel.send(f'キーワード "{keyword}" を登録しました')

    else:
        # その他のメッセージ処理
        keyword = message.content.lower()
        query = keywords_ref.where('keyword', '==', keyword).get()

        for doc in query:
            data = doc.to_dict()
            image_url = data['imageurl']

            # 画像送信部分
            import aiohttp
            import io

            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        with io.BytesIO(data) as file:
                            await message.channel.send(file=discord.File(file, 'image.png'))
            break
        else:
            return

# Botの実行
client.run('')