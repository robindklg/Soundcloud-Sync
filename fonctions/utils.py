""" Fonctions diverses utiles pour la GUI de Soundcloud Sync. """

import os
import json
import configparser
from pathlib import Path
import shutil
import requests

from PyQt6 import QtWidgets, QtGui, QtCore
import soundcloud


CONFIG_PATH = Path(os.getcwd()).resolve() / "config.conf"
VERSION = "1.2"


def fenetre_info(titre, message, window_object=None):
    """ Petite fenetre pour afficher un message. """

    window_message = QtWidgets.QMessageBox(window_object)
    window_message.setText(message)
    window_message.setWindowTitle(titre)
    window_message.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    window_message.exec() 


def remplacer_caract_spec(chaine):
    """ Remplacer les caractères modifiés par leur équivalent. """

    dict_caracteres = {"？": "?",
                       "＊": "*",
                       "＞": ">",
                       "/": "",
                       "⧸": "",
                       "：": ":",
                       "｜": "|",
                       '＂': '"',
                       "ë": 'ë',
                       "＜": "<"}
    for c in dict_caracteres:
        chaine = chaine.replace(c, dict_caracteres[c])

    return chaine


def load_json_file(json_path):
    """" Charger les données de synchronisation depuis le fichier JSON. """

    if Path(json_path).exists():
        try:
            with open(json_path, 'r') as file:
                json_data = json.load(file)
        except FileNotFoundError:
            fenetre_info("Erreur", "Le répertoire de synchronisation est invalide.")
    else:  # Créer le fichier s'il n'existe pas.
        json_data = {
            "musiques": [],
            "albums": [],
            "playlists": [],
            "artistes": [],
            "likes": [],
        }
        with open(json_path, 'w') as file:
            json.dump(json_data, file, indent=4)

    return json_data


def write_json_file(json_path, json_data):
    """ Sauvegarder les données à synchroniser dans le fichier JSON. """

    try:
        with open(json_path, 'w') as file:
            json.dump(json_data, file, indent=4)
    except FileNotFoundError:
        fenetre_info("Erreur", "Le chemin du fichier de synchronisation JSON est invalide.")


def load_local_files(library_path):
    """ Charger dans un dictionnaire l'arborescence du répertoire. """

    nb_total_file = 0
    arborescence = {}
    chemin_bibliotheque = Path(library_path)

    for dossier in chemin_bibliotheque.iterdir():
        if dossier.is_dir():
            if dossier.name == "Musiques":
                arborescence[dossier.name] = []
                for musique in dossier.iterdir():
                    arborescence[dossier.name].append(f"/Musiques/{remplacer_caract_spec(musique.stem)}")
                    nb_total_file += 1
            else:
                arborescence[dossier.name] = {}
                for e in dossier.iterdir():
                    if e.is_dir():
                        arborescence[dossier.name][remplacer_caract_spec(e.name)] = []
                        for fichier in Path(dossier / e).iterdir():
                            path_fichier = f"/{dossier.name}/{remplacer_caract_spec(e.name)}/{remplacer_caract_spec(fichier.stem)}"
                            arborescence[dossier.name][remplacer_caract_spec(e.name)].append(path_fichier)
                            nb_total_file += 1

    return arborescence, nb_total_file


def verification_parametres():
    """ Vérifie la validité des paramètres. """

    json_path, sc_object = True, True
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    # Vérifier le fichier de configuration.
    if not "GLOBAL" in config:
        fenetre_info("Erreur", "Le fichier de configuration est introuvable:\n"
                                     f"{CONFIG_PATH}")
    if not config["GLOBAL"]["LOCAL_PATH"] or not Path(config["GLOBAL"]["LOCAL_PATH"]).exists():
        json_path = False
    if config["GLOBAL"]["TOKEN"]:
        sc_object = soundcloud.SoundCloud(auth_token=config["GLOBAL"]["TOKEN"])
        try:
            assert sc_object.is_auth_token_valid()
        except AssertionError:
            sc_object = False
    else:
        sc_object = False

    return json_path, sc_object


def recuperer_parametres():
    """ Charger les paramètres. """

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    json_path = config["GLOBAL"]["LOCAL_PATH"] + os.sep + config["GLOBAL"]["SYNCONF_FILE"]
    json_data = load_json_file(json_path)
    sc_object = soundcloud.SoundCloud(auth_token=config["GLOBAL"]["TOKEN"])

    return config, json_path, json_data, sc_object


def trouver_ligne_url(object_window, url):
    """ Obtenir le numéro de ligne de la table des éléments à synchroniser avec l'URL. """

    for row in range(object_window.table_elements.rowCount()):
        item = object_window.table_elements.item(row, 1)
        if item.text() == url:
            return row
    return None


def definir_status_element(object_window, ligne, texte, couleur):
    """ Définir le status d'un élément dans le tableau affiché. """

    status = QtWidgets.QTableWidgetItem(texte)
    status.setForeground(QtGui.QColor(couleur))
    object_window.table_elements.setItem(ligne, 2, status)


def actualiser_interface(object_window):
    """ Actualise les éléments affichés. """

    # Récupération des données et mise à jour de la barre de status.
    try:
        config, json_path, json_data, sc_object = recuperer_parametres()
    except requests.exceptions.ConnectionError as e:
        print(f"Erreur: Connexion impossible ({e})")
        raise ConnectionError("Connexion impossible")
    arborescence, nb_total_file = load_local_files(config["GLOBAL"]["LOCAL_PATH"])
    object_window.label_nb_fichiers.setText(f"Nombre de fichiers téléchargés: {nb_total_file}")
    object_window.label_compte.setText(f"Connecté avec le compte de {sc_object.get_me().username}")

    object_window.table_elements.setRowCount(0)
    # Mise à jour de chaque élément playlist du tableau.
    for playlist in json_data["playlists"]:
        row_position = object_window.table_elements.rowCount()
        nom_playlist = str(Path(playlist[1]).name)
        object_window.table_elements.insertRow(row_position)
        object_window.table_elements.setItem(row_position, 1, QtWidgets.QTableWidgetItem(playlist[0][8:]))
        object_window.table_elements.setItem(row_position, 0, QtWidgets.QTableWidgetItem(playlist[1]))
        # Mise à jour du status de la synchronisation de l'élément.
        if row_position in object_window.synchros_en_cours:
            definir_status_element(object_window, row_position,f"synchronisation en cours...", "orange")
        else:
            try:
                nb_titres_playlist_sc = len(sc_object.resolve(playlist[0]).tracks)
            except AttributeError:
                supprimer_element(object_window, row_position, json_path)
            else:
                if not nom_playlist in arborescence["Playlists"]:
                    status = QtWidgets.QTableWidgetItem("0 musiques téléchargées")
                    status.setForeground(QtGui.QColor("red"))
                    definir_status_element(object_window, row_position, f"0/{nb_titres_playlist_sc} musiques téléchargées",
                                           "red")
                else:
                    nb_fichiers_telecharges = len(arborescence["Playlists"][nom_playlist])
                    if nb_fichiers_telecharges == nb_titres_playlist_sc:
                        definir_status_element(object_window, row_position,
                                               f"{nb_titres_playlist_sc}/{nb_titres_playlist_sc} musiques téléchargées",
                                               "green")
                    else:
                        definir_status_element(object_window, row_position, f"{nb_fichiers_telecharges}"
                                                                            f"/{nb_titres_playlist_sc} musiques téléchargées",
                                               "orange")
    # Mise à jour de chaque élément albums du tableau.
    for album in json_data["albums"]:
        nom_album = str(Path(album[1]).name)
        row_position = object_window.table_elements.rowCount()
        object_window.table_elements.insertRow(row_position)
        object_window.table_elements.setItem(row_position, 1, QtWidgets.QTableWidgetItem(album[0][8:]))
        object_window.table_elements.setItem(row_position, 0, QtWidgets.QTableWidgetItem(album[1]))
        # Mise à jour du status de la synchronisation de l'élément.
        if row_position in object_window.synchros_en_cours:
            definir_status_element(object_window, row_position,f"synchronisation en cours...",
                                   "orange")
        else:
            try:
                nb_titres_album_sc = len(sc_object.resolve(album[0]).tracks)
            except AttributeError:
                supprimer_element(object_window, row_position, json_path)
            else:
                if not nom_album in arborescence["Albums"]:
                    status = QtWidgets.QTableWidgetItem("0 musiques téléchargées")
                    status.setForeground(QtGui.QColor("red"))
                    definir_status_element(object_window, row_position, f"0/{nb_titres_album_sc} musiques téléchargées",
                                           "red")
                else:
                    nb_fichiers_telecharges = len(arborescence["Albums"][nom_album])
                    if nb_fichiers_telecharges == nb_titres_album_sc:
                        definir_status_element(object_window, row_position,
                                               f"{nb_titres_album_sc}/{nb_titres_album_sc} musiques téléchargées",
                                               "green")
                    else:
                        definir_status_element(object_window, row_position, f"{nb_fichiers_telecharges}"
                                                                   f"/{nb_titres_album_sc} musiques téléchargées",
                                               "orange")
    # Mise à jour de chaque élément artist du tableau.
    for artiste in json_data["artistes"]:
        nom_artiste = str(Path(artiste[1]).name)
        row_position = object_window.table_elements.rowCount()
        object_window.table_elements.insertRow(row_position)
        object_window.table_elements.setItem(row_position, 1, QtWidgets.QTableWidgetItem(artiste[0][8:]))
        object_window.table_elements.setItem(row_position, 0, QtWidgets.QTableWidgetItem(artiste[1]))
        # Mise à jour du status de la synchronisation de l'élément.
        if row_position in object_window.synchros_en_cours:
            definir_status_element(object_window, row_position,f"synchronisation en cours...", "orange")
        else:
            nb_titres_artist_sc = sc_object.resolve(artiste[0]).track_count
            if not nom_artiste in arborescence["Artistes"]:
                status = QtWidgets.QTableWidgetItem("0 musiques téléchargées")
                status.setForeground(QtGui.QColor("red"))
                definir_status_element(object_window, row_position, f"0/{nb_titres_artist_sc} musiques téléchargées", "red")
            else:
                nb_fichiers_telecharges = len(arborescence["Artistes"][nom_artiste])
                if nb_fichiers_telecharges == nb_titres_artist_sc:
                    definir_status_element(object_window, row_position,
                                           f"{nb_titres_artist_sc}/{nb_titres_artist_sc} musiques téléchargées", "green")
                else:
                    definir_status_element(object_window, row_position, f"{nb_fichiers_telecharges}"
                                                               f"/{nb_titres_artist_sc} musiques téléchargées", "orange")
    # Mise à jour des likes de profils sur le tableau.
    for profil in json_data["likes"]:
        nom_profil = str(Path(profil[1]).name)
        row_position = object_window.table_elements.rowCount()
        object_window.table_elements.insertRow(row_position)
        object_window.table_elements.setItem(row_position, 1, QtWidgets.QTableWidgetItem(profil[0][8:]))
        object_window.table_elements.setItem(row_position, 0, QtWidgets.QTableWidgetItem(profil[1]))
        # Mise à jour du status de la synchronisation de l'élément.
        if row_position in object_window.synchros_en_cours:
            definir_status_element(object_window, row_position,f"synchronisation en cours...", "orange")
        else:
            nb_titres_likes_sc = 0
            try:
                for like in list(sc_object.get_user_likes(sc_object.resolve(profil[0]).id)):
                    if isinstance(like, soundcloud.TrackLike):
                        nb_titres_likes_sc += 1
            except AttributeError:
                supprimer_element(object_window, row_position, json_path)
            else:
                if not nom_profil in arborescence["Likes"]:
                    status = QtWidgets.QTableWidgetItem("0 musiques téléchargées")
                    status.setForeground(QtGui.QColor("red"))
                    definir_status_element(object_window, row_position, f"0/{nb_titres_likes_sc} musiques téléchargées",
                                           "red")
                else:
                    nb_fichiers_telecharges = len(arborescence["Likes"][nom_profil])
                    if nb_fichiers_telecharges == nb_titres_likes_sc:
                        definir_status_element(object_window, row_position,
                                               f"{nb_titres_likes_sc}/{nb_titres_likes_sc} musiques téléchargées",
                                               "green")
                    else:
                        definir_status_element(object_window, row_position, f"{nb_fichiers_telecharges}"
                                                f"/{nb_titres_likes_sc} musiques téléchargées","orange")
    # Mise à jour de chaque musique seule du tableau.
    for track in json_data["musiques"]:
        row_position = object_window.table_elements.rowCount()
        object_window.table_elements.insertRow(row_position)
        object_window.table_elements.setItem(row_position, 1, QtWidgets.QTableWidgetItem(track[0][8:]))
        object_window.table_elements.setItem(row_position, 0, QtWidgets.QTableWidgetItem(track[1]))
        if row_position in object_window.synchros_en_cours:
            definir_status_element(object_window, row_position,f"synchronisation en cours...", "orange")
        else:
            if track[1] in arborescence["Musiques"]:
                definir_status_element(object_window, row_position, "Musique téléchargée", "green")
            else:
                definir_status_element(object_window, row_position,
                                       "Musiques non téléchargée", "red")


class ActualiserAffichage(QtCore.QThread):
    """ Classe pour lancer la fonction actualiser_interface dans un Thread avec QThread. """

    sync_finished = QtCore.pyqtSignal(object)

    def __init__(self, window_object, parent=None):
        super().__init__(parent)
        self.window_object = window_object

    def run(self):
        actualiser_interface(self.window_object)
        self.sync_finished.emit(None)


def supprimer_element(object_window, index, json_path):
    """ Supprimer un élément. """

    url = object_window.table_elements.item(index, 1).text()
    object_window.table_elements.removeRow(index)
    json_content = load_json_file(json_path)

    for cat in json_content:
        cat_id = 0
        for element in json_content[cat]:
            if element[0].endswith(url):
                if object_window.auto_download_action.isChecked():
                    # Suppréssion du fichier ou du dossier local.
                    config = configparser.ConfigParser()
                    config.read(CONFIG_PATH)
                    path_to_remove = Path(config["GLOBAL"]["LOCAL_PATH"]) / Path(
                        json_content[cat][cat_id][1][1:])
                    if path_to_remove.is_dir():
                        shutil.rmtree(path_to_remove)
                    else:
                        for fichier in path_to_remove.parent.iterdir():
                            if fichier.is_file() and fichier.stem == path_to_remove.name:
                                fichier.unlink()
                                break

                del json_content[cat][cat_id]
                break
            cat_id += 1

    write_json_file(json_path, json_content)


def supprimer_tout_elements(object_window, json_path):
    """ Vider la liste des éléments à synchroniser après confirmation. """

    # Créer une boite de dialogue pour demander confirmation avant de supprimer tout les éléments.
    boite_dialogue = QtWidgets.QMessageBox()
    boite_dialogue.setWindowTitle("Confirmation")
    boite_dialogue.setText("Êtes-vous sûr de vouloir supprimer tous les éléments à synchroniser ?")
    bouton_oui = boite_dialogue.addButton("Oui", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
    boite_dialogue.addButton("Non", QtWidgets.QMessageBox.ButtonRole.RejectRole)
    boite_dialogue.exec()
    if boite_dialogue.clickedButton() == bouton_oui:
        Path(json_path).unlink()  # Suppréssion du fichier JSON.
        object_window.table_elements.setRowCount(0)  # Vider la table des éléments affichée.
    else:
        pass


def modifier_parametre_config(cle, valeur):
    """ Modifie une valeur booléenne dans le fichier de configuration. """

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    config["GLOBAL"][cle] = str(valeur)
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)
