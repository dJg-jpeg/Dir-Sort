from collections import Counter
import sys
import re
from shutil import unpack_archive, rmtree
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


async def make_dirs(path):
    sort_folders = []
    for folder_name in FOLDERS_NAMES:
        new_folder = path / folder_name
        if await new_folder.exists():
            sort_folders.append(path / folder_name)
            continue
        await (path / folder_name).mkdir()
    return sort_folders


async def move_files(files, dirs):
    for file_type in files:
        for file_path in file_type:
            files[files.index(file_type)][files[files.index(file_type)].index(file_path)] = \
                dirs[files.index(file_type)] / file_path.name
            await file_path.replace(dirs[files.index(file_type)] / file_path.name)
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
    rename_tasks = []
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
            files[files.index(category)][category.index(content)] = content.parent / filename
            rename_tasks.append(create_task(AsyncPath(content).rename(AsyncPath(content).parent / filename)))
    await gather(*rename_tasks)


async def remove_empty_dirs(path):
    inner_folders = []
    async for content in path:
        if await content.is_dir() and content.name not in FOLDERS_NAMES:
            rmtree(content)
    await gather(*inner_folders)


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
        make_new_folders = create_task(make_dirs(p))
        await make_new_folders
        new_dirs = make_new_folders.result()
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
