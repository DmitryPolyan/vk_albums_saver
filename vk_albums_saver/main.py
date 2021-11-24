import vk_api
import sys
import os
import asyncio
import aiohttp
import aiofiles


# TODO: Добавить логирование
def auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция. """
    key = input("Enter authentication code: ")
    remember_device = True
    return key, remember_device


def auth(user_mail: str, user_password: str) -> vk_api.VkApi:
    """Функция аутентификации"""
    vk_session = vk_api.VkApi(user_mail, user_password, auth_handler=auth_handler)
    vk_session.auth()
    vk = vk_session.get_api()
    return vk


async def download(queue, session, newpath: str, i: int):
    """Асинхронный загрузчик фотографий"""
    counter = 0
    while True:
        try:
            url = queue.get_nowait()
            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.read()
                    async with aiofiles.open(newpath+"/"+str(i), 'wb') as file:
                        await file.write(data)
                else:
                    print(f"{url.split('/')[-1]} raised error {r.status_code}")
                queue.task_done()
                print(f"{i} downloaded")
        except asyncio.TimeoutError:
            # TODO Переделать через повторение запроса
            counter += 1
            if counter < 3:
                print(f"Отправляем {url} в очередь снова")
                queue.put_nowait(url)
            else:
                print(f"Не удалось скачать {url}")
        except:
            return


async def get_photos(conn: vk_api.VkApi, album_id: str, album_title: str, album_size: int):
    """Сохраняет фото в папку в корне"""
    # TODO: Добавить возможность выбора папки
    newpath = os.path.join(sys.path[0], album_title)
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    photos = conn.photos.get(album_id=album_id, count=1000)
    urls = [i["sizes"][-1]["url"] for i in photos["items"]]
    queue = asyncio.Queue()
    for url in urls:
        queue.put_nowait(url)
    timeout = aiohttp.ClientTimeout(total=7)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        await asyncio.gather(*[download(queue, session, newpath, i) for i in range(album_size)])


async def download_album(conn: vk_api.VkApi):
    """Сохраняет фотографии из альбома по указаному ID поользователя и альбома"""
    albums = conn.photos.getAlbums()['items']
    albums_info = dict()

    if albums:
        for album in albums:
            albums_info[album["id"]] = (album["title"], album["size"])
            print(f'id: {album["id"]} - name: {album["title"]} - size: {album["size"]}')
    else:
        print("empty")
    while True:
        # limit of vk_api - maximum 1000 photos in album
        print("""Instruction:
        "WARNING"
        Album size limit - no more than 1000 photos 
        
        Enter id for download album
        Enter "exit" for exit
        Enter "all" for download all albums
        Enter "refresh" for refresh album list """)
        command = input("Your chose: ")

        if command == 'exit':
            break
        elif command == "refresh":
            await download_album(conn)
            break
        elif command == "all":
            try:
                for album in albums:
                    await get_photos(conn, str(album["id"]), *albums_info[album["id"]])
                    await download_album(conn)
                    break
            except Exception as e:
                print(f"err: {e}")
        elif command.isalnum():
            try:
                await get_photos(conn, command, *albums_info[int(command)])
            except Exception as e:
                print(f"err: {e}")
        else:
            print('Wrong format of command or id')


async def main():
    user_mail = input('Введите почту или телефон: ')
    user_password = input('Введите пароль от учетной записи: ')
    conn = auth(user_mail, user_password)
    action = input('Для выхода нажмите n, для продолжения нажмите Entr ')
    if action not in "nNтТ" or not action:
        await download_album(conn)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
