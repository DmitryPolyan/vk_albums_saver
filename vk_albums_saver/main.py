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


async def download(queue, session, newpath: str):
    """Асинхронный загрузчик фотографий"""
    while True:
        try:
            url = queue.get_nowait()
            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.read()
                    async with aiofiles.open(newpath+"/"+url.split('/')[-1], 'wb') as file:
                        await file.write(data)
                else:
                    print(f"{url.split('/')[-1]} raised error {r.status_code}")
                queue.task_done()
        except asyncio.QueueEmpty:
            print("Download is done")
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
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[download(queue, session, newpath) for i in range(album_size)])


async def download_album(conn: vk_api.VkApi):
    """Сохраняет фотографии из альбома по указаному ID поользователя и альбома"""
    albums = conn.photos.getAlbums()['items']
    albums_info = dict()

    if albums:
        for album in albums:
            albums_info[album["id"]] = (album["title"], album["size"])
            print(f'{album["id"]} - {album["title"]} - {album["size"]}')
    else:
        print("empty")
    while True:
        # TODO: Добавить возможность скачать сразу все альбомы и обновление списка альбомов
        # TODO: Предупрждение об ограничении размера альбомов в 1000 фото (ограничение API)
        album_id = input('Enter id of album for download or enter exit: ')
        if album_id == 'exit':
            break
        elif album_id.isalnum():
            try:
                await get_photos(conn, album_id, *albums_info[int(album_id)])
            # TODO: Реализовать корректную обработку ошибок
            except:
                print("Something wrong")
        else:
            print('Wrong format of id')


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
