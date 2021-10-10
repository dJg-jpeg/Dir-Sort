from pathlib import Path
import sys
import re
import shutil


def get_cmd_args():
    if len(sys.argv) != 2:
        print("Insert only 1 argument")
    else:
        return sys.argv[1]


def check_file_extension(extension):
    if extension == 'jpeg' or extension == 'jpg' or extension == 'png' or extension == 'svg':
        return 'image'
    elif extension == 'avi' or extension == 'mp4' or extension == 'mov' or extension == 'mkv':
        return 'video'
    elif extension == 'mp3' or extension == 'ogg' or extension == 'wav' or extension == 'amr':
        return 'audio'
    elif (extension == 'doc' or extension == 'docx' or extension == 'txt' or extension == 'pdf'
          or extension == 'xlsx' or extension == 'pptx'):
        return 'document'
    elif extension == 'zip' or extension == 'gz' or extension == 'tar':
        return 'archive'
    return 'unknown'


def find_all_files(path, images, videos, documents, audios, archives, unknown):
    for content in path:
        if content.is_dir() and (content.name == 'images' or
                                 content.name == 'documents' or
                                 content.name == 'video' or
                                 content.name == 'audio' or
                                 content.name == 'archives'):
            continue
        elif content.is_dir():
            inside_dirs = find_all_files(content.iterdir(), images, videos, documents, audios, archives, unknown)
            images = inside_dirs[0]
            videos = inside_dirs[1]
            audios = inside_dirs[2]
            documents = inside_dirs[3]
            archives = inside_dirs[4]
            unknown = inside_dirs[5]
        else:
            extension = get_filename_and_extension(content.name)[1]
            if check_file_extension(extension) == 'image':
                images.append(content)
            elif check_file_extension(extension) == 'video':
                videos.append(content)
            elif check_file_extension(extension) == 'audio':
                audios.append(content)
            elif check_file_extension(extension) == 'document':
                documents.append(content)
            elif check_file_extension(extension) == 'archive':
                archives.append(content)
            else:
                unknown.append(content)
    return images, videos, audios, documents, archives, unknown


def make_dirs(path):
    images = check_is_dir_exist(path / 'images')
    videos = check_is_dir_exist(path / 'videos')
    audios = check_is_dir_exist(path / 'audios')
    documents = check_is_dir_exist(path / 'documents')
    archives = check_is_dir_exist(path / 'archives')
    unknown = check_is_dir_exist(path / 'unknown')
    if images is False:
        (path / 'images').mkdir()
        images = check_is_dir_exist(path / 'images')
    if videos is False:
        (path / 'videos').mkdir()
        videos = check_is_dir_exist(path / 'videos')
    if audios is False:
        (path / 'audios').mkdir()
        audios = check_is_dir_exist(path / 'audios')
    if documents is False:
        (path / 'documents').mkdir()
        documents = check_is_dir_exist(path / 'documents')
    if archives is False:
        (path / 'archives').mkdir()
        archives = check_is_dir_exist(path / 'archives')
    if unknown is False:
        (path / 'unknown').mkdir()
        unknown = check_is_dir_exist(path / 'unknown')
    return images, videos, audios, documents, archives, unknown


def check_is_dir_exist(path):
    if path.exists() is True:
        return path
    return path.exists()


def move_files(files, dirs):
    for image in files[0]:
        image.replace(dirs[0] / image.name)
        files[0][files[0].index(image)] = dirs[0] / image.name
    for video in files[1]:
        video.replace(dirs[1] / video.name)
        files[1][files[1].index(video)] = dirs[1] / video.name
    for audio in files[2]:
        audio.replace(dirs[2] / audio.name)
        files[2][files[2].index(audio)] = dirs[2] / audio.name
    for document in files[3]:
        document.replace(dirs[3] / document.name)
        files[3][files[3].index(document)] = dirs[3] / document.name
    for archive in files[4]:
        (dirs[4] / get_filename_and_extension(archive.name)[0]).mkdir()
        archive.replace(dirs[4] / get_filename_and_extension(archive.name)[0] / archive.name)
        files[4][files[4].index(archive)] = dirs[4] / get_filename_and_extension(archive.name)[0]
        archive_path = dirs[4] / get_filename_and_extension(archive.name)[0] / archive.name
        archive_dir = dirs[4] / get_filename_and_extension(archive.name)[0]
        unpack_archives(archive_path, archive_dir)
    for unknown in files[5]:
        unknown.replace(dirs[5] / unknown.name)
        files[5][files[5].index(unknown)] = dirs[5] / unknown.name
    return files


def unpack_archives(archive, new_dir_path):
    shutil.unpack_archive(archive, new_dir_path)


def get_filename_and_extension(filename):
    index = filename.find('.')
    return filename[:index], filename[index + 1:]


def rename_files(files):
    for category in files:
        for content in category:
            filename = (normalize(get_filename_and_extension(content.name)[0]) +
                        '.' + get_filename_and_extension(content.name)[1])
            content.rename(content.parent / filename)
            files[files.index(category)][category.index(content)] = content.parent / filename
    return files


def remove_empty_dirs(path):
    for content in path:
        if content.is_dir() is True and len(list(content.iterdir())) > 0:
            remove_empty_dirs(content.iterdir())
        elif content.is_dir() is True and len(list(content.iterdir())) == 0:
            content.rmdir()
        else:
            continue


def normalize(name):
    table_symbols = ('абвгґдеєжзиіїйклмнопрстуфхцчшщюяыэАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЮЯЫЭьъЬЪ',
                     (
                         *u'abvhgde', 'ye', 'zh', *u'zyi', 'yi', *u'yklmnoprstuf', 'kh', 'ts',
                         'ch', 'sh', 'shch', 'yu', 'ya', 'y', 'ye', *u'ABVHGDE', 'Ye', 'Zh', *u'ZYI',
                         'Yi', *u'YKLMNOPRSTUF', 'KH', 'TS', 'CH', 'SH', 'SHCH', 'YU', 'YA', 'Y', 'YE',
                         *(u'_' * 4)
                     )
                     )
    map_cyr_to_latin = {ord(src): dest for src, dest in zip(*table_symbols)}
    rx = re.compile(r"[^\w_]")
    return rx.sub('_', name.translate(map_cyr_to_latin))


if __name__ == '__main__':
    p = Path(get_cmd_args())
    im = []
    vi = []
    au = []
    do = []
    ar = []
    un = []
    if p.is_dir():
        all_files = find_all_files(p.iterdir(), im, vi, au, do, ar, un)
        all_files = rename_files(all_files)
        new_dirs = make_dirs(p)
        new_files = move_files(all_files, new_dirs)
        remove_empty_dirs(p.iterdir())
        remove_empty_dirs(p.iterdir())
        print(all_files)
    else:
        print('It is not a directory , please insert a valid directory path')
