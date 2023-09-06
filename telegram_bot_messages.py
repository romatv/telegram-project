welcome_message = 'Welcome to Spotygo Bot!\n' \
                  'This bot allows you to download your favourite Spotify playlist in just a couple clicks!\n\n' \
                  'To start - send me a link to your Spotify Playlist!\n\n' \
                  'Note: you can\'t download Dynamic playlists like "Top 50 songs for you" because of security reasons. \n\n' \
                  'If you have any questions type /help'

help_message = 'Welcome to Spotygo Bot!\n' \
               'This Help section will answer some of your common questions.\n\n' \
               '1. What playlists can I download?\n' \
               'Any Spotify playlist which is not hidden from public.\n' \
               'Dynamic playlists like "Top 50 songs for you" are not available,\n' \
               'because Spotify services require your authorization for getting these playlists data.\n' \
               '2. How to start?\n' \
               'To initiate the process just send SpotyGo the link to your playlist.\n' \
               'The link should look like this https://open.spotify.com/...\n\n' \
               '3. What will happen next?\n' \
               'You will receive ZIP archive with all of your songs in mp4 format. ' \
               'It may take some time to download,\n' \
               'so wait a bit while our services work for you.\n\n' \
               '4. Why some of my songs are missing?\n' \
               'Due to policy of some songs, they could be age restrited or not available for download.\n' \
               'Usually it is not more than 1-2% of total playlist size.\n\n' \
               '5. Is it safe?\n' \
               'Yes, it is totally safe. We don\'t request any user data other than playlist link.'

successful_download_message = 'Congrats!\n' \
                              'Download was successful!\n\n' \
                              'To download another playlist, send new link to SpotyGo.'

error_incorrect_link_message = 'Sorry but link you sent is not valid.\n\n' \
                               'Please send link that looks like this:\n\n' \
                               'https://open.spotify.com/...\n\n' \
                               'For FAQ type /help'

error_no_link_message = 'Sorry but the message you sent is not a link.\n\n' \
                        'Please send link that looks like this:\n\n' \
                        'https://open.spotify.com/...\n\n' \
                        'For FAQ type /help'

error_one_link_message = 'You can download only 1 playlist at a time.\n\n' \
                         'For FAQ type /help'

restriction_message = 'You\'ve reached your limit of downloads.\n' \
                      'We set limit to 2 playlists per week, as this helps to reduce SpotyGo load.\n\n' \
                      'If you would like to increase your limit,\n' \
                      'please contact SpotyGo.'

initialize_message = 'Working on it...'

file_error_message = 'Sorry, there was an error while sending file.'


my_messages = {'welcome_message': welcome_message,
               'help_message': help_message,
               'successful_download_message': successful_download_message,
               'error_one_link_message': error_one_link_message,
               'error_no_link_message': error_no_link_message,
               'error_incorrect_link_message': error_incorrect_link_message,
               'restriction_message': restriction_message,
               'initialize_message': initialize_message,
               'file_error_messagee': file_error_message}
