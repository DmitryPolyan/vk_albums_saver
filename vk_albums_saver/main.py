import vk_api
import sys
import os
import requests


def handle_auth():
    user_mail = input('Введите почту или телефон: ')
    user_password = input('Введите пароль от учетной записи: ')
    return user_mail, user_password


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


def get_photos(vk, album_id):
    """Сохраняет фото в папку в корне"""
    newpath = os.path.join(sys.path[0], album_id)
    # TODO: Название папки по названию альбома
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    photos = vk.photos.get(album_id=album_id, count=1000)
    for i in photos["items"]:
        url = i["sizes"][-1]["url"]
        file_id = i["id"]
        # TODO: Реализовать асинхронность
        download(url, file_id, newpath)


def download_album(vk: vk_api.VkApi):
    """Сохраняет фотографии из альбома по указаному ID поользователя и альбома"""
    albums = vk.photos.getAlbums()['items']
    print(albums)
    if albums:
        for album in albums:
            print(f'{album["id"]} - {album["title"]} - {album["size"]}')
    else:
        print("empty")
    while True:
        album_id = input('Enter id of album for download or enter exit: ')
        if album_id == 'exit':
            break
        elif album_id.isalnum():
            try:
                get_photos(vk, album_id)
            # TODO: Реализовать корректную обработку ошибок
            except:
                print("Something wrong")
        else:
            print('Wrong format of id')


def main():
    user_mail, user_password = handle_auth()
    vk = auth(user_mail, user_password)
    action = input('Для выхода нажмите n, для продолжения любую клавишу')
    if action not in "nNтТ":
        download_album(vk)


if __name__ == "__main__":
    main()
