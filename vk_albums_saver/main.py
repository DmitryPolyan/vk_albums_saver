import vk_api
import sys
import os
import requests


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


def download(url, file_id, newpath):
    """Скачивает фото по URL"""
    r = requests.get(url)
    if r.status_code == 200:
        with open(f'/{newpath}/{file_id}.jpg', 'wb') as f:
            f.write(r.content)
    else:
        print(f'{file_id} raised error {r.status_code}')


def get_photos(session, album_id):
    """Сохраняет фото в папку в корне"""
    # TODO: Добавить возможность выбора папки
    newpath = os.path.join(sys.path[0], album_id)
    # TODO: Название папки по названию альбома
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    photos = session.photos.get(album_id=album_id, count=1000)
    # TODO: Добавить отображение процентов или отображение имен файлов
    for i in photos["items"]:
        url = i["sizes"][-1]["url"]
        file_id = i["id"]
        # TODO: Реализовать асинхронность
        download(url, file_id, newpath)


def download_album(session: vk_api.VkApi):
    """Сохраняет фотографии из альбома по указаному ID поользователя и альбома"""
    albums = session.photos.getAlbums()['items']
    if albums:
        for album in albums:
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
                get_photos(session, album_id)
            # TODO: Реализовать корректную обработку ошибок
            except:
                print("Something wrong")
        else:
            print('Wrong format of id')


def main():
    user_mail = input('Введите почту или телефон: ')
    user_password = input('Введите пароль от учетной записи: ')
    session = auth(user_mail, user_password)
    action = input('Для выхода нажмите n, для продолжения любую клавишу')
    if action not in "nNтТ":
        download_album(session)


if __name__ == "__main__":
    main()
