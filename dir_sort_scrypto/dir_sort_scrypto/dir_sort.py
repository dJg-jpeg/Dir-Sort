from collections import Counter
import sys
import re
from shutil import unpack_archive
from asyncio import create_task, run, gather
from aiopath import AsyncPath


FOLDERS_NAMES = ('image', 'video', 'audio', 'document', 'archive', 'unknown')
FILE_TYPES_EXTENSIONS = (
                         ('.jpeg', '.jpg', '.png', '.svg'),
                         ('.avi', '.mp4', '.mov', '.mkv'),
                         ('.mp3', '.ogg', '.wav', '.amr'),
                         ('.doc', '.docx', '.txt', '.pdf', '.xlsx', '.pptx'),
                         ('.zip', '.gz', '.tar')
                        )


def get_cmd_args():
    if len(sys.argv) != 2:
        print("Insert only 1 argument")
    else:
        return sys.argv[1]


def check_file_extension(extension):
    for file_types in FILE_TYPES_EXTENSIONS:
        if extension in file_types:
            return FOLDERS_NAMES[FILE_TYPES_EXTENSIONS.index(file_types)]
    return FOLDERS_NAMES[5]


async def find_all_files(path, files):
    inner_folders = []
    async for content in path:
        if await content.is_dir():
            inner_folders.append(create_task(find_all_files(content.iterdir(), files)))
        elif content.name not in FOLDERS_NAMES:
            extension = check_file_extension(get_filename_and_extension(content)[1])
            files[FOLDERS_NAMES.index(extension)].append(content)
    await gather(*inner_folders)


def make_dirs(path):
    sort_folders = []
    for folder_name in FOLDERS_NAMES:
        if not (path / folder_name).exists():
            (path / folder_name).mkdir()
        sort_folders.append(path / folder_name)
    return sort_folders


async def move_files(files, dirs):
    for file_type in files:
        for file_path in file_type:
            await file_path.replace(dirs[files.index(file_type)] / file_path.name)
            files[files.index(file_type)][files[files.index(file_type)].index(file_path)] = \
                dirs[files.index(file_type)] / file_path.name
    for archive in files[4]:
        path_to_archive_dir = dirs[4] / get_filename_and_extension(archive)[0]
        archive_path = path_to_archive_dir / archive.name
        path_to_archive_dir.mkdir()
        archive.replace(archive_path)
        files[4][files[4].index(archive)] = path_to_archive_dir
        unpack_archives(archive_path, path_to_archive_dir)
        archive_path.unlink()
    return files


def unpack_archives(archive, new_dir_path):
    unpack_archive(archive, new_dir_path)


def get_filename_and_extension(filepath):
    return filepath.stem, filepath.suffix


async def normalize_filenames(files):
    filenames = []
    for category in files:
        filenames.append([])
        for content in category:
            filename = normalize(get_filename_and_extension(content)[0]) + get_filename_and_extension(content)[1]
            if filename in filenames[-1]:
                filenames[-1].append(filename)
                filename = f'{get_filename_and_extension(content)[0]}' \
                           f'({Counter(filenames[-1])[filename] - 1})' \
                           f'{get_filename_and_extension(content)[1]}'
            else:
                filenames[-1].append(filename)
            content = await AsyncPath(content).rename(AsyncPath(content).parent / filename)
            files[files.index(category)][category.index(content)] = content.parent / filename
    return files


async def remove_empty_dirs(path):
    async for content in path:
        if content.is_dir() is True and len(list(content.iterdir())) > 0:
            await remove_empty_dirs(content.iterdir())
        if content.is_dir() is True and len(list(content.iterdir())) == 0:
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


async def main():
    p = AsyncPath(get_cmd_args())
    if await p.is_dir():
        all_files = [[], [], [], [], [], []]
        find_files = create_task(find_all_files(p.iterdir(), all_files))
        await find_files
        rename_all_files = create_task(normalize_filenames(all_files))
        new_dirs = make_dirs(p)
        move_all_files = create_task(move_files(all_files, new_dirs))
        await rename_all_files
        await move_all_files
        all_files = move_all_files.result()
        remove_empty = create_task(remove_empty_dirs(p.iterdir()))
        await remove_empty
        print("Sorted files : \n ", all_files)
    else:
        print('It is not a directory , please insert a valid directory path')


if __name__ == '__main__':
    run(main())
