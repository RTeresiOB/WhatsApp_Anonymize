#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 15:08:59 2020

Parse and anonymize Whatsapp messages

@author: RobertTeresi
"""

# Import libraries
import pandas as pd
import re
import os
from pathlib import Path
from datetime import datetime
import spacy
import names
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

# FILE PARAMETERS #
TEXT_PATH = Path(Path.home() /
                 'Dropbox/CoViD_ED_TF/WhatsApp Chat sample.txt')
KEY_FOLDER = Path(Path.home() /
                  'Dropbox/CoViD_ED_TF/Public_Key/')
DATA_DIR = Path(Path.home() /
                   'Dropbox/CoViD_ED_TF/')


class Encryptor(object):
    """
    Generate public key and encrypt identifiers.

    key_folder is where the key will be stored. It should be a PosixPath
        (made using Path from pathlib).
    """

    def __init__(self, key_folder):
        try:
            self.load_public_key(key_folder)
        except Exception:
            try:
                os.mkdir(key_folder)
            except FileExistsError:
                pass
            self.generate_public_key(key_folder)
            self.load_public_key(key_folder)

    def generate_keys(self, key_folder):
        """
        Generate the public key and store it in a file.

        Only run this if there is no existing key.
        """
        print("Generating key")
        private_key = rsa.generate_private_key(
            public_exponent=849745,
            key_size=4096,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
                )

        with open(Path(key_folder / 'public_key.pem'), 'wb') as file:
            file.write(pem)

        pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
                )

        with open(Path(key_folder / 'private_key.pem'), 'wb') as file:
            file.write(pem)

    def load_public_key(self, key_folder):
        """Attach public key to class from file."""
        with open(Path(key_folder / 'public_key.pem'), 'rb') as file:
            self.public_key = serialization.load_pem_public_key(
                    file.read(),
                    backend=default_backend()
                    )
        with open(Path(key_folder / 'private_key.pem'), "rb") as file:
            self.private_key = serialization.load_pem_private_key(
                    file.read(),
                    password=None,
                    backend=default_backend()
                    )

    def encrypt(self, identifier):
        """Encrypt identifier and return encrypted bytearray."""
        identifier = identifier.encode('utf-8')
        return(self.public_key.encrypt(
                    identifier,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                        )
                    )
               )

    def decrypt(self, encrypted_message):
        """Decrypt encrypted message."""
        return(self.private_key.decrypt(
                            encrypted_message,
                            padding.OAEP(
                                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                algorithm=hashes.SHA256(),
                                label=None
                                )
                            )
               )


class TextParser(object):
    """Class that opens and parses files, then turns them into Texts."""

    def __init__(self, path, print_contents=False):
        """Read in data from file."""
        with open(path) as file:
            self.file_contents = file.read()

            if print_contents:
                print('Printing file contents...')
                print(self.file_contents)

    def parse_times(self, file):
        """Take in file and return Datetimes of each Whatsapp message."""
        times = re.findall(r'\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2} [AP]M - ',
                           file)
        times = [re.search(r'\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2} [AP]M',
                           time).group(0) for time in times]
        return([datetime.strptime(time,
                                  '%m/%d/%y, %I:%M %p') for time in times])

    def parse_into_texts(self):
        """Take larger file and parse it into discrete messages."""
        times = self.parse_times(self.file_contents)

        texts = re.split(r'\n\n\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2} [AP]M - ',
                         self.file_contents)
        texts = [re.sub(r'\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2} [AP]M - ',
                        '', text) for text in texts]

        self.WhatsAppTexts = [WhatsAppText(text, time)
                              for text, time in tuple(zip(texts, times))]


class WhatsAppText(object):
    """Class associated with a single Whatsapp message."""

    msg, sender, alias = None, None, None

    def __init__(self, text, time):
        """Initialize the class."""
        self.user_msg = bool(re.search(r': ', text))
        self.time_sent = time
        if self.user_msg:
            if len(re.split(r': ', text)) > 2:
                self.msg = ': '.join(re.split(': ', text)[1:])
            else:
                self.msg = self.preprocess_text(re.split(': ', text)[1])

            self.sender = re.split(': ', text)[0]
        else:
            self.msg = text

    def preprocess_text(self, text):
        """Preprocess texts before putting them into Spacy model.

        For now the only thing I really want to do is fix a quirk where the
        format "Name- " thinks that Name- is one token.
        """
        print(text)
        matches = re.findall(r'^([A-Z][a-z]+)\- |[\.\?\!] ([A-Z][a-z]+)\- ',
                             text)
        for match in matches:
            for group in match:
                # Match contains name and empty string
                if group:
                    text = re.sub((group + r'\- '),
                                  (group + r' - '),
                                  text)
        return(text)


class Entity_Recognizer:
    """Replace indentifiers with anonymous tags/identities."""

    def __init__(self):
        """Initialize nlp engine."""
        self.nlp = spacy.load("en_core_web_sm")
        self.entlist = list()
        self.names = list(pd.read_csv('/Users/RobertTeresi/Dropbox/'
                                      'CoViD_ED_TF/listofnames.csv')['Name'])
        self.names = [str(x).capitalize() for x in self.names]

    def parse_entity(self, ent):
        """Make sure entity is person. Add to list if not on it."""
        replacestring = ''
        lastent = list()
        for token in ent:
            # If word not in names list but in vocab then this is a mistake
            if ((token.text not in self.names) and
                    (token.text in self.nlp.vocab)):
                if token.text == '’s':
                    replacestring += '\'s'
                else:
                    replacestring = ' '.join([replacestring, token.text])
                lastent = list()
            else:
                # Check if this entity is in our list
                if token.text.capitalize() in self.entlist:
                    pass
                else:
                    self.entlist.append(token.text)

                # If previous entity, check if full name is in list
                if lastent:
                    if (' '.join([lastent[0], token.text.capitalize()])
                            not in self.entlist):
                        self.entlist.append(' '.join([lastent[0],
                                                     token.text.capitalize()]))
                lastent = [token.text.capitalize()]

                if 'PERSON' in replacestring:
                    pass
                else:
                    replacestring = ' '.join([replacestring, 'PERSON'])

        return(replacestring.strip())

    def anonymize_text(self, text, iteration=None):
        """Anonymize text."""
        def obscure_phone_numbers(text):
            """Replace phone numbers with NUMBER."""
            return(re.sub(r'\+1 \(\d{3}\) \d{3}\-\d{4}', 'NUMBER', text))

        self.anontext = self.nlp(text)
        text2 = str(self.anontext.text)
        reidx = 0  # Need to shift replace index after first entity replaced
        textlen = len(text2)

        # In the first iteration we use Spacy's ML alg for entity detection
        if iteration == 0:
            for ent in self.anontext.ents:
                if ent.label_ == 'PERSON':
                    replacer = self.parse_entity(ent)
                    text2 = (text2[:(ent.start_char + reidx)] +
                             replacer + text2[(ent.end_char + reidx):])

                    # Following works because ents go from left to right.
                    reidx = len(text2) - textlen

            return(obscure_phone_numbers(text2))
        # In the second iteration
        elif iteration == 1:
            for token in self.anontext:
                if str(token.text).capitalize() in self.entlist:
                    startchar = token.idx
                    endchar = startchar + len(token.text) + 1
                    text2 = (text2[:(startchar + reidx)] + 'PERSON' +
                             text2[(endchar + reidx):])
                    reidx = len(text2) - textlen
            return(obscure_phone_numbers(text2))
        else:
            raise ValueError('Enter either 0 or 1 as the iteration parameter.')

    def delete_entlist(self):
        """Clear list so that names no longer exist."""
        self.entlist = list()


class WhatsAppAnonymizer(object):
    """Main class that calls other classes and uploads data."""

    aliasdict = {}
    encryptdict = {}

    def __init__(self, text_path, key_folder, data_dir):
        """Initialize class."""
        # Initialize paths needed
        self.text_path = text_path
        self.key_folder = key_folder
        self.data_dir = data_dir

        # Initialize classes
        self.textparser = TextParser(path=text_path)
        self.textparser.parse_into_texts()
        self.encryptor = Encryptor(key_folder=key_folder)
        self.anonymizer = Entity_Recognizer()

    def encrypt_identities(self):
        """Encrypt the sender."""
        for i in range(len(self.textparser.WhatsAppTexts)):
            x = self.textparser.WhatsAppTexts[i].sender
            if x is None:
                continue
            elif x in self.encryptdict.keys():
                self.textparser.WhatsAppTexts[i].sender = self.encryptdict[x]
            else:
                encrypted_id = self.encryptor.encrypt(x)
                self.encryptdict.update({x: encrypted_id})
                self.textparser.WhatsAppTexts[i].sender = encrypted_id

    def create_alias(self, encrypted_id):
        """Create unique aliases for each encrypted identifier."""
        def unique_name(namedict):
            """Ensure aliases aren't repeated."""
            name = names.get_full_name()
            while name in namedict.items():
                name = names.get_full_name()
            return(name)

        if encrypted_id is None:
            self.aliasdict.update({encrypted_id: 'Whatsapp'})
        elif encrypted_id in self.aliasdict.keys():
            pass
        else:
            self.aliasdict.update({encrypted_id: unique_name(self.aliasdict)})

    def anonymize_text_bodies(self):
        """Call anonymize function from encryptor class."""
        # Run twice - first time builds dictionary, second time replaces based
        # on all recognized entities.
        for j in range(0, 2):
            for i in range(len(self.textparser.WhatsAppTexts)):
                x = self.textparser.WhatsAppTexts[i].msg
                self.textparser.WhatsAppTexts[i].msg = (self.anonymizer.
                                                        anonymize_text(x, j))

    def upload_file(self, append=False):
        """Create dataframe and upload it as a .csv.
        
        This will need some work. As of right not it won't do very well
        appending texts that were sent at the same time as the last text of 
        the last upload. I don't think this is a problem for my current use
        case, but I will add it to the to-do list.
        """
        def append_row(self,text):
            textdf.append({'sender': text.sender,
                           'alias': self.aliasdict[text.sender],
                           'msg': text.msg,
                           'time': text.time_sent},
                          ignore_index=True)

        if append:
            textdf = self.old_data
        else:
            textdf = pd.DataFrame(columns=['sender',
                                           'alias',
                                           'msg',
                                           'time'])

        for text in self.textparser.WhatsAppTexts:
            if append & 
                    (text.time_sent <= self.old_data.iloc[-1]['time']):
                continue
            self.create_alias(text.sender)
            print(text.msg)
            textdf = self.append_row(text)

        textdf.to_csv(self.data_dir / 'encrypted_whatsapp_msgs.csv')

        def append_file(self):
            """Add to existing data if wanted."""
            if os.path.exists(self.data_dir /
                              'encrypted_whatsapp_msgs.csv'):
                console_msg = ('You already have encrypted messages saved.\n'
                               'Enter in 1 to overwrite the existing data\n'
                               'Enter in 2 to append to the existing data\n'
                               'Enter in 3 to exit without saving\n\n.')
                print(console_msg)
                response = int(input())
                count = 0
                while response not in [1, 2, 3]:
                    if count > 2:
                        print('Retries exceeded--script closing. '
                              'Please report this if it is an error.')
                        exit()
                    print("It seems you have entered in an incorrect input.")
                    print(console_msg)
                    response = int(input())

                if response == 3:
                    exit()  # Exit the script without saving

                elif response == 2:
                    self.old_data = pd.read_csv(self.data_dir /
                                                'encrypted_whatsapp_msgs.csv')
                    self.upload_file(append=True)
                else:
                    # Overwrite by uploading_file directly
                    self.upload_file()
            else:
                self.upload_file()


def main():
    """Control execution of class functions."""
    global anonymizer
    anonymizer = WhatsAppAnonymizer(TEXT_PATH, KEY_FOLDER, DATA_DIR)
    anonymizer.encrypt_identities()
    anonymizer.anonymize_text_bodies()
    anonymizer.append_file()


if __name__ == '__main__':
    main()
