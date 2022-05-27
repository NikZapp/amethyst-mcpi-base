import queue
import time

from .connection import Connection
from datetime import datetime
from threading import Thread, Event


class Plugin:
    name = 'mcpi_chat'
    author = 'NikZapp'
    messages = queue.Queue()
    parsed = 0
    config = {'log_path': '',
              'time_formatting': '',
              'queue_messages': False,
              'server_motd': ''}
    players = {}
    thread = None
    stop_event = Event()

    def setup(event_dict):
        if Plugin.config['log_path'] == '':
            Plugin.config['log_path'] = input('Path to latest log file:')
        Plugin.messages = queue.Queue()
        log_file = open(Plugin.config['log_path'], 'r')
        Plugin.parsed = len(log_file.readlines())
        log_file.close()
        Plugin.thread = Thread(target=Plugin.update_thread, args=(event_dict,))
        Plugin.thread.start()

    def decompose_line(line, event_dict):
        decomposition = {'raw_text': line}
        try:
            decomposition['raw_type'] = line[1:5]
            if decomposition['raw_type'] == 'CHAT':
                if decomposition['raw_text'][8:].startswith(f'<{Plugin.config["server_motd"]}>'):
                    pass  # Server message, ignore.
                else:
                    decomposition['from_client'] = not decomposition['raw_text'].endswith(
                        'joined the game')  # Remove duplicate join message (CHAT and INFO)
                    # Check if it's a disconnect message
                    try:
                        if decomposition['raw_text'].split()[-4:] == ['disconnected', 'from', 'the', 'game']:
                            # Someone may have left OR someone is faking it
                            # We check if the username is in the list
                            decomposition['username'] = decomposition['raw_text'][
                                                     8:(decomposition['raw_text'].rindex('disconnected') - 1)]
                            if decomposition['username'] in Plugin.players:
                                decomposition['type'] = 'leave'
                                return decomposition
                            else:
                                pass  # It's a chat message, continue
                    except IndexError:
                        pass  # The message is too small, so it's definitely not a disconnect message

                    # Check if it is a death message
                    try:
                        if decomposition['raw_text'].split()[-2:] == ['has', 'died']:
                            # Someone may have died OR someone is faking it
                            # We check if the username is in the list
                            decomposition['username'] = decomposition['raw_text'][
                                                     8:(decomposition['raw_text'].rindex('disconnected') - 1)]
                            if decomposition['username'] in Plugin.players:
                                decomposition['type'] = 'death'
                                return decomposition
                            else:
                                pass  # It's a chat message, continue
                    except IndexError:
                        pass  # The message is too small, so it's definitely not a death message
                    if decomposition['from_client']:
                        decomposition['type'] = 'chat'
                        decomposition['username'] = decomposition['raw_text'][9:decomposition['raw_text'].index('>')]
                        decomposition['message'] = decomposition['raw_text'][len(decomposition['username']) + 11:]
                    else:
                        decomposition['type'] = 'none'
                    return decomposition
            if decomposition['raw_type'] == 'INFO':
                # Check if it is a player joining
                if decomposition['raw_text'].split()[-4:-2] == ['Has', 'Joined']:
                    decomposition['username'] = decomposition['raw_text'][
                                             8:(decomposition['raw_text'].rindex('Has') - 1)]
                    decomposition['ip'] = decomposition['raw_text'].split()[-1][:-1]
                    decomposition['type'] = 'join'
                    return decomposition
            decomposition['type'] = 'none'
            return decomposition
        except IndexError:
            decomposition['type'] = 'none'
            return decomposition  # Line is too short, probably a system message

    def update(event_dict):
        slice_len = len(datetime.now().strftime(Plugin.config['time_formatting']))
        Plugin.messages = queue.Queue()
        log_file = open(Plugin.config['log_path'], 'r')
        lines = log_file.readlines()
        log_file.close()

        # Queue found messages
        if len(lines) - Plugin.parsed > 0:  # If there are new lines
            for line in lines[-(len(lines) - Plugin.parsed):]:
                if Plugin.config['queue_messages']:
                    Plugin.messages.put(line[slice_len:-1])
                new_event_dict = Plugin.decompose_line(line[slice_len:-1], event_dict)
                message_type = new_event_dict['type']

                if message_type == 'join':
                    Plugin.players[new_event_dict['username']] = {'ip': new_event_dict['ip']}

                event_dict['amethyst']['event'](['mcpi_chat', 'raw'], new_event_dict)
                event_dict['amethyst']['event'](['mcpi_chat', message_type], new_event_dict)

                if message_type == 'leave':
                    Plugin.players.pop(new_event_dict['username'])

        Plugin.parsed = len(lines)

    def update_thread(event_dict):
        while not Plugin.stop_event.is_set():
            time.sleep(1)
            Plugin.update(event_dict)

    def send(message):
        connection = Connection("localhost", 4711)
        connection.send(b"chat.post", message)
        connection.close()

    def stop(event_dict):
        Plugin.stop_event.set()
        Plugin.thread.join()

    events = {'amethyst': {
                  'setup': setup,
                  'stop': stop
    }}
