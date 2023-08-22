import os
import shutil
from datetime import datetime

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from pytube import Search, YouTube
from mutagen.mp4 import MP4

load_dotenv()
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')
SCOPE = 'playlist-read-private'

# Authenticate application using spotipy.
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=SCOPE))


def create_zipfile(name: str, folder_path: str):
    """Creates ZIP archive with all downloaded songs, log.txt and saves it into the folder"""

    shutil.make_archive(base_name=folder_path + f'/{name}', format='zip', root_dir=folder_path)


def delete_files(folder_path: str):
    """Deletes all downloaded files and their folder."""

    shutil.rmtree(folder_path)


def get_songs_list(playlist_id: str, marker: str) -> list:
    """Returns a list of song full names.

    Gets the dictionary with playlist songs data. Specifications of this dictionary are in readme file.
    Then appends items as 'artist_name - song_name' to the list songs_list and returns it.
    """

    # Initial values of 'offset' and 'limit' are set for pagination.
    # We use pagintation to increase limit of tracks returned from a playlist,
    # because Spotify can return max. 100 items per 1 playlist request.
    offset = 0
    limit = 100
    songs_list = []

    while True:
        if marker == 'album':
            album_results = sp.album_tracks(playlist_id, market='from_token')
            for item in album_results['items']:
                track_name = item['name']
                artists = item['artists']
                artists_names = ', '.join([artist['name'] for artist in artists])
                songs_list.append(f'{artists_names} - {track_name}')
            break

        if marker == 'playlist':
            playlist_results = sp.playlist_items(playlist_id, fields='items(track(name, artists(name)))',
                                                 market='from_token',
                                                 offset=offset, limit=limit)
            for item in playlist_results['items']:
                track_name = item['track']['name']
                artists = item['track']['artists']
                artists_names = ', '.join([artist['name'] for artist in artists])
                songs_list.append(f'{artists_names} - {track_name}')

            # Next lines describe the logic of pagination.
            # If number of items rcvd less than 100, it means we reached the last portion of playlist.
            # Otherwise, len will be 100 and offset will change from 0 to 100, 100 to 200...
            # So in 245 songs playlist, 1st batch will rcv songs 0-100 (offset 0). Next 100-200 (offset 100).
            # Next 200-245 (offset 200). Limit stays 100, as it's Spotify Max per request.
            if len(playlist_results['items']) < limit:
                break
            offset += limit

    return songs_list


def get_song_url(song_name: str) -> str:
    """Returns link to a first video found on YouTube by requested song_name."""

    yt_search = Search(f'{song_name}')
    return yt_search.results[0].watch_url


def update_metadata(file_path: str, artist: str, song_name: str):
    """Function updates artist name and song name metadata of the mp4 file in a given path."""

    # Load the mp4 file and set values for mp4 tags.
    audio = MP4(file_path)
    artist_tag = '\xa9ART'
    song_name_tag = '\xa9nam'

    # Set metadata fields
    audio[artist_tag] = artist
    audio[song_name_tag] = song_name

    # Save the changes
    audio.save()


def download_song(path: str, song_name: str, playlist_id: str):
    """ Downloads audio streams from YouTube and writes results into Log file.

    Downloads mp4 file named as song_name into a folder named as playlist_id.
    Also creates log file in the same folder and appends each download result in it
    """

    downloaded_file_name = f'{song_name}.mp4'
    if not os.path.exists(f'{path}/{downloaded_file_name}'):
        with open(f'{path}/log-{playlist_id}.txt', mode='a', encoding='UTF-8') as file:
            file.write(f'{datetime.utcnow()} UTC\n')

            try:
                # Get url of the first video in search with song_name and download its max quality audio stream.
                youtube = YouTube(get_song_url(song_name))
                audio_stream = youtube.streams.get_audio_only()
                audio_stream.download(filename=downloaded_file_name, output_path=path)
                file.write(f'{downloaded_file_name} downloaded!\n')
                # Update metadata of file such as artist name and song name.
                update_metadata(file_path=f'{path}/{downloaded_file_name}',
                                artist=song_name.split('-')[0],
                                song_name=song_name.split('-')[1])
            except Exception as error:
                file.write(f' Unsuccessful download! For song: {downloaded_file_name}\n')
                print(error)


def start_download_operation(playlist_id: str, playlist_type: str):
    """Function responsible for downloading files process.

    If yes - creates a new folder in project directory with a name of playlist id.
    Then loops over range of playlist length to download each song from it into the folder, and finally
    places all files into a ZIP file.
    """

    final_songs_list = get_songs_list(playlist_id, playlist_type)
    files_path = f'./Downloads/{playlist_id}'
    os.makedirs(files_path, exist_ok=True)  # Creates a new folder in a project path if it doesn't exist.
    print('Commence of downloading operation.')
    for song in final_songs_list:
        download_song(files_path, song, playlist_id)
    print('Operation completed!')
    create_zipfile(name=playlist_id, folder_path=files_path)
