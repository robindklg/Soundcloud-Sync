""" Fichier principal à éxécuter pour ouvrir l'utilitaire de synchronisation
après avoir vérifié les données."""

import sys
import os
import webbrowser
import requests
from pathlib import Path

import soundcloud
from PyQt6 import QtWidgets, QtGui, QtCore""" Fichier principal à éxécuter pour ouvrir l'utilitaire de synchronisation
après avoir vérifié les données."""

import sys
import os
import webbrowser
import requests
from pathlib import Path

import soundcloud
from PyQt6 import QtWidgets, QtGui, QtCore

from fonctions import utils, config_windows, sync_fonctions

import faulthandler
faulthandler.enable()


class MainWindow(QtWidgets.QMainWindow):
    """ Fenetre principale de SoundCloud Sync affichant les éléments à synchroniser. """

    config_window = None
    actualisation_en_cours = False
    synchros_en_cours = []

    def __init__(self):
        super().__init__()

        # Initialisation de la fenêtre principale
        self.setWindowTitle(f"Soundcloud Sync - {Path(config['GLOBAL']['LOCAL_PATH']).name}")
        self.setWindowIcon(QtGui.QIcon(f"ressources{os.sep}logo.png"))
        self.setGeometry(0, 0, 900, 400)

        # Layout principal vertical
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Layout du haut de la fenetre.
        layout_haut = QtWidgets.QHBoxLayout()
        layout_haut.setContentsMargins(5, 5, 5, 5)
        self.bouton_sync = QtWidgets.QPushButton("Tout Synchroniser")
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.bouton_sync.setFont(font)
        self.bouton_sync.setMinimumSize(150, 40)
        self.bouton_sync.clicked.connect(lambda: self.sync_all_bouton())
        self.input_url = QtWidgets.QLineEdit()
        self.boutton_ajouter = QtWidgets.QPushButton("Ajouter un lien")
        self.boutton_ajouter.setMinimumSize(100, 30)
        self.input_url.returnPressed.connect(lambda: (self.ajouter_lien()))
        self.boutton_ajouter.clicked.connect(lambda: (self.ajouter_lien()))
        layout_haut.addWidget(self.bouton_sync)
        layout_haut.addWidget(self.input_url)
        layout_haut.addWidget(self.boutton_ajouter)

        # Widget de la liste des contenus à synchroniser sous forme de tableau.
        self.table_elements = QtWidgets.QTableWidget()
        self.table_elements.setColumnCount(3)
        self.table_elements.setHorizontalHeaderLabels(["Element", "URL", "Status"])
        self.table_elements.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table_elements.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_elements.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_elements.customContextMenuRequested.connect(self.menu_contextuel)

        # Ajouter le layout du haut et le widget tableau au main layout.
        main_layout.addLayout(layout_haut)
        main_layout.addWidget(self.table_elements)
        central_widget = QtWidgets.QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Barre de menu en haut de la fenetre.
        menubar = self.menuBar()
        # Menu paramètres.
        parametres_menu = menubar.addMenu("Paramètres")
        self.bloquer_suppression_action = QtGui.QAction("Ne pas supprimer les fichiers en trop", self)
        self.bloquer_suppression_action.setCheckable(True)
        self.bloquer_suppression_action.setChecked(config.getboolean("GLOBAL", "SUPPRIMER_FICHIERS"))
        self.bloquer_suppression_action.triggered.connect(lambda: utils.modifier_parametre_config("SUPPRIMER_FICHIERS",
                                                                                                  self.bloquer_suppression_action.isChecked()))
        parametres_menu.addAction(self.bloquer_suppression_action)
        self.convert_mp3_action = QtGui.QAction("Convertir les fichiers téléchargés au format mp3", self)
        self.convert_mp3_action.setCheckable(True)
        self.convert_mp3_action.setChecked(config.getboolean("GLOBAL", "CONVERT_TO_MP3"))
        self.convert_mp3_action.triggered.connect(
            lambda: utils.modifier_parametre_config("CONVERT_TO_MP3", self.convert_mp3_action.isChecked()))
        parametres_menu.addAction(self.convert_mp3_action)
        self.auto_download_action = QtGui.QAction("Synchroniser les éléments lorsqu'ils sont ajoutés", self)
        self.auto_download_action.setCheckable(True)
        self.auto_download_action.setChecked(config.getboolean("GLOBAL", "AUTO_DOWNLOAD"))
        self.auto_download_action.triggered.connect(
            lambda: utils.modifier_parametre_config("AUTO_DOWNLOAD", self.auto_download_action.isChecked()))
        parametres_menu.addAction(self.auto_download_action)
        self.remove_local_action = QtGui.QAction("Supprimer aussi les fichiers locaux lors de la suppréssion d'un élément", self)
        self.remove_local_action.setCheckable(True)
        self.remove_local_action.setChecked(config.getboolean("GLOBAL", "REMOVE_LOCAL"))
        self.remove_local_action.triggered.connect(
            lambda: utils.modifier_parametre_config("REMOVE_LOCAL", self.remove_local_action.isChecked()))
        parametres_menu.addAction(self.remove_local_action)
        # Menu Actions.
        actions_menu = menubar.addMenu("Actions")
        actions_config = QtGui.QAction("Configuration", self)
        actions_config.triggered.connect(self.config_parametres)
        actualiser_action = QtGui.QAction("Actualiser les éléments affichés", self)
        actualiser_action.triggered.connect(lambda: self.actualiser_affichage_thread())
        supprimer_tout_action = QtGui.QAction("Supprimer tous les éléments", self)
        supprimer_tout_action.triggered.connect(lambda: utils.supprimer_tout_elements(self, json_path))
        actions_menu.addAction(actions_config)
        actions_menu.addAction(actualiser_action)
        actions_menu.addAction(supprimer_tout_action)
        # Menu à propos.
        apropos_menu = menubar.addMenu("A propos")
        github_action = QtGui.QAction("Github", self)
        github_action.triggered.connect(lambda: webbrowser.open("https://github.com/Robin-mlh/Soundcloud-Sync"))
        apropos_menu.addAction(github_action)
        aide_action = QtGui.QAction("Aide", self)
        aide_action.triggered.connect(lambda: webbrowser.open("https://github.com/Robin-mlh/Soundcloud-Sync/tree/main?tab=readme-ov-file#param%C3%A8tres"))
        apropos_menu.addAction(aide_action)
        version_action = QtGui.QAction("Version", self)
        version_action.triggered.connect(lambda: utils.fenetre_info("Version", f"Version {utils.VERSION}", self))
        apropos_menu.addAction(version_action)

        # Barre de status en bas de la fenetre.
        self.barre_status = self.statusBar()
        self.label_compte = QtWidgets.QLabel()
        self.barre_status.addPermanentWidget(self.label_compte)
        self.label_nb_fichiers = QtWidgets.QLabel()
        self.barre_status.addPermanentWidget(QtWidgets.QWidget(), 1)
        self.label_actualisation = QtWidgets.QLabel()
        self.barre_status.addPermanentWidget(self.label_actualisation)
        self.barre_status.addPermanentWidget(QtWidgets.QWidget(), 1)
        self.barre_status.addPermanentWidget(self.label_nb_fichiers)

        self.actualiser_affichage_thread()


    def actualiser_affichage_thread(self):
        """ Déclencher le Thread d'actualisation de l'affichage. """

        if not self.actualisation_en_cours:
            self.label_actualisation.setText("Actualisation en cours...")
            self.actualisation_en_cours = True
            self.sync_thread = utils.ActualiserAffichage(self)
            self.sync_thread.finished.connect(self.fin_actualisation_affichage_thread)
            self.sync_thread.start()


    def fin_actualisation_affichage_thread(self):
        """ Fin du Thread d'actulisation de l'affichage. """

        self.actualisation_en_cours = False
        self.label_actualisation.setText("")


    def ajouter_lien(self):
        """ Ajouter un lien au fichier JSON et à l'interface s'il est valide. """

        url = self.input_url.text()
        if url:
            if not url.startswith("https://soundcloud.com/"):
                utils.fenetre_info("Erreur", "Le lien fourni est invalide.\n"
                                       "Incluez uniquement des playlistes, albums, musiques ou utilisateurs Soundcloud.\n"
                                       "Exemple de format: 'https://soundcloud.com/ak420-anarkotek'", self)
            else:
                json_content = utils.load_json_file(json_path)
                content = sc_object.resolve(url)
                if isinstance(content, soundcloud.Track):  # Le lien fourni est une musique.
                    titre = utils.remplacer_caract_spec(content.title)
                    if not [url, f"/Musiques/{titre}"] in json_content["musiques"]:
                        json_content["musiques"].append((url, f"/Musiques/{titre}"))
                elif isinstance(content, soundcloud.AlbumPlaylist):
                    listname = utils.remplacer_caract_spec(content.title)
                    if content.is_album:  # Le lien fourni est un album.
                        if not [url, f"/Albums/{listname}/"] in json_content["albums"]:
                            json_content["albums"].append((url, f"/Albums/{listname}/"))
                    else:  # Le lien fourni est une playliste.
                        if not [url, f"/Playlists/{listname}/"] in json_content["playlists"]:
                            json_content["playlists"].append((url, f"/Playlists/{listname}/"))
                elif isinstance(content, soundcloud.User):
                    if url.endswith("likes"):
                        username = utils.remplacer_caract_spec(content.username)
                        if not [url, f"/Likes/{content.username}/"] in json_content["likes"]:
                            json_content["likes"].append((url, f"/Likes/{username}/"))
                    else:
                        username = utils.remplacer_caract_spec(content.username)
                        if not [url, f"/Artistes/{content.username}/"] in json_content["artistes"]:
                            json_content["artistes"].append((url, f"/Artistes/{username}/"))
                else:  # Le lien n'est ni une musique, ni un album, ni une playliste, ni un artiste.
                    utils.fenetre_info("Erreur", "Le lien fourni est invalide.\n"
                                           "Incluez uniquement des playlistes, albums, musiques ou utilisateurs Soundcloud.\n"
                                           "Exemple de format: 'https://soundcloud.com/ak420-anarkotek'", self)
                utils.write_json_file(json_path, json_content)  # Mettre à jour le fichier JSON.

            self.input_url.clear()  # Vider la barre d'input.
            self.actualiser_affichage_thread()
            if self.auto_download_action.isChecked():
                numero_ligne = utils.trouver_ligne_url(self, url[8:])
                while not numero_ligne:
                    numero_ligne = utils.trouver_ligne_url(self, url[8:])
                self.sync_element_menu(numero_ligne)


    def sync_all_bouton(self):
        """ Action du bouton pour synchroniser tous les éléments. """

        self.bouton_sync.setText("Synchronisation...")
        self.bouton_sync.setEnabled(False)
        self.sync_thread = sync_fonctions.SyncAllThread(self, json_path, sc_object)
        self.sync_thread.finished.connect(self.synchronisation_terminee)
        self.sync_thread.start()


    def synchronisation_terminee(self):
        """Réinitialise l'état du bouton après la synchronisation."""

        self.bouton_sync.setText("Tout Synchroniser")
        self.bouton_sync.setEnabled(True)
        self.actualiser_affichage_thread()

    def fenetre_config_fermee(self):
        """ La fenêtre de configuration a été fermée. """

        self.actualiser_affichage_thread()

    def config_parametres(self):
        """ Ouvre la fenetre de configuration importée. """

        if self.config_window and not self.config_window.isVisible():
            # Vérifier si la fenetre de configuration est ouverte,
            # mettre self.config_window à None si ce n'est pas le cas.
            self.config_window = None
        if not self.config_window:
            # Si la fenetre n'est pas ouverte, l'ouvrir.
            self.config_window = config_windows.ConfigApp()
            self.config_window.config_closed.connect(self.fenetre_config_fermee)
            self.config_window.show()
        else:  # Si la fenetre est deja ouverte, la mettre au premier plan.
            self.config_window.activateWindow()
            self.config_window.raise_()


    def menu_contextuel(self, position):
        """ Défini le menu contextuel (clique droit) sur la liste des éléments. """

        row = self.table_elements.currentRow()
        if row >= 0:
            menu = QtWidgets.QMenu(self)
            action_copier_url = QtGui.QAction("Copier l'URL", self)
            action_copier_url.triggered.connect(lambda: self.copier_element(row))
            action_supprimer_element = QtGui.QAction("Supprimer l'élément", self)
            action_supprimer_element.triggered.connect(lambda: utils.supprimer_element(self, row, json_path))
            action_synchroniser_element = QtGui.QAction("Synchroniser l'élément", self)
            action_synchroniser_element.triggered.connect(lambda: self.sync_element_menu(row))
            menu.addAction(action_supprimer_element)
            menu.addAction(action_synchroniser_element)
            menu.addAction(action_copier_url)
            menu.exec(self.table_elements.viewport().mapToGlobal(position))


    def copier_element(self, row):
        """ Copier l'URL de l'élément sélectionné. """

        url = self.table_elements.item(row, 1).text()
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(url)


    def sync_element_menu(self, row):
        """ Synchroniser uniquement l'élément sélectionné dans le menu contextuel. """

        json_element = ["https://" + self.table_elements.item(row, 1).text(),
                        self.table_elements.item(row, 0).text()]
        library_path = str(Path(json_path).parent)
        self.sync_thread = sync_fonctions.SyncElementThread(self, library_path, sc_object, json_element)
        self.sync_thread.start()


def main():
    global config
    global json_path
    global sc_object

    print("Chargement de l'application...")
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("QStatusBar::item { border: 0px solid black }; ")

    # Vérifier la connexion internet.
    try:
        requests.get("https://soundcloud.com", timeout=5)
    except requests.exceptions.ConnectionError as e:
        print(f"Erreur: Connexion impossible ({e})")
        utils.fenetre_info("Erreur", "Soundcloud n'est pas joignable.\n"
                                     "Vérifiez votre connexion internet")
        sys.exit()
    # Vérifier les paramètres (dans le fichier de configuration).
    json_path, sc_object = utils.verification_parametres()
    if not sc_object and not json_path:  # Si des paramètres sont invalides:
        utils.fenetre_info("Erreur", "Les paramètres sont manquants ou invalides.")
    elif not sc_object:
        utils.fenetre_info("Erreur", "Le Token d'authentification est invalide.")
    elif not json_path:
        utils.fenetre_info("Erreur", "Le répertoire de synchronisation est invalide.")
    if not json_path or not sc_object:
        # Ouvrir la fenetre de configuration.
        config_window = config_windows.ConfigApp()
        config_window.show()
        app.exec()

    # Récupérer les paramètres depuis le fichier de configuration.
    config, json_path, json_data, sc_object = utils.recuperer_parametres()
    # Créer les dossiers des catégories de contenu s'ils n'existe pas.
    tracks_path = Path(config["GLOBAL"]["LOCAL_PATH"]) / "Musiques"
    tracks_path.mkdir(parents=True, exist_ok=True)
    tracks_path = Path(config["GLOBAL"]["LOCAL_PATH"]) / "Albums"
    tracks_path.mkdir(parents=True, exist_ok=True)
    tracks_path = Path(config["GLOBAL"]["LOCAL_PATH"]) / "Playlists"
    tracks_path.mkdir(parents=True, exist_ok=True)
    tracks_path = Path(config["GLOBAL"]["LOCAL_PATH"]) / "Artistes"
    tracks_path.mkdir(parents=True, exist_ok=True)
    tracks_path = Path(config["GLOBAL"]["LOCAL_PATH"]) / "Likes"
    tracks_path.mkdir(parents=True, exist_ok=True)

    # Lancer la fenetre principale de Soundcloud Sync.
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

from fonctions import utils, config_windows, sync_fonctions


class MainWindow(QtWidgets.QMainWindow):
    """ Fenetre principale de SoundCloud Sync affichant les éléments à synchroniser. """

    config_window = None
    actualisation_en_cours = False

    def __init__(self):
        super().__init__()

        # Initialisation de la fenêtre principale
        self.setWindowTitle("Soundcloud Sync")
        self.setWindowIcon(QtGui.QIcon(f"ressources{os.sep}logo.png"))
        self.setGeometry(0, 0, 900, 400)

        # Layout principal vertical
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Layout du haut de la fenetre.
        layout_haut = QtWidgets.QHBoxLayout()
        layout_haut.setContentsMargins(5, 5, 5, 5)
        self.bouton_sync = QtWidgets.QPushButton("Tout Synchroniser")
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.bouton_sync.setFont(font)
        self.bouton_sync.setMinimumSize(150, 40)
        self.bouton_sync.clicked.connect(lambda: self.sync_all_bouton())
        self.input_url = QtWidgets.QLineEdit()
        self.boutton_ajouter = QtWidgets.QPushButton("Ajouter un lien")
        self.boutton_ajouter.setMinimumSize(100, 30)
        self.input_url.returnPressed.connect(lambda: (self.ajouter_lien()))
        self.boutton_ajouter.clicked.connect(lambda: (self.ajouter_lien()))
        layout_haut.addWidget(self.bouton_sync)
        layout_haut.addWidget(self.input_url)
        layout_haut.addWidget(self.boutton_ajouter)

        # Widget de la liste des contenus à synchroniser sous forme de tableau.
        self.table_elements = QtWidgets.QTableWidget()
        self.table_elements.setColumnCount(3)
        self.table_elements.setHorizontalHeaderLabels(["Element", "URL", "Status"])
        self.table_elements.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table_elements.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_elements.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_elements.customContextMenuRequested.connect(self.menu_contextuel)

        # Ajouter le layout du haut et le widget tableau au main layout.
        main_layout.addLayout(layout_haut)
        main_layout.addWidget(self.table_elements)
        central_widget = QtWidgets.QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Barre de menu en haut de la fenetre.
        menubar = self.menuBar()
        # Menu paramètres.
        parametres_menu = menubar.addMenu("Paramètres")
        self.bloquer_suppression_action = QtGui.QAction("Ne pas supprimer les fichiers en trop", self)
        self.bloquer_suppression_action.setCheckable(True)
        self.bloquer_suppression_action.setChecked(config.getboolean("GLOBAL", "SUPPRIMER_FICHIERS"))
        self.bloquer_suppression_action.triggered.connect(lambda: utils.modifier_parametre_config("SUPPRIMER_FICHIERS",
                                                                                                  self.bloquer_suppression_action.isChecked()))
        parametres_menu.addAction(self.bloquer_suppression_action)
        self.convert_mp3_action = QtGui.QAction("Convertir les fichiers téléchargés au format mp3", self)
        self.convert_mp3_action.setCheckable(True)
        self.convert_mp3_action.setChecked(config.getboolean("GLOBAL", "CONVERT_TO_MP3"))
        self.convert_mp3_action.triggered.connect(
            lambda: utils.modifier_parametre_config("CONVERT_TO_MP3", self.convert_mp3_action.isChecked()))
        parametres_menu.addAction(self.convert_mp3_action)
        self.auto_download_action = QtGui.QAction("Synchroniser les éléments lorsqu'ils sont ajoutés", self)
        self.auto_download_action.setCheckable(True)
        self.auto_download_action.setChecked(config.getboolean("GLOBAL", "AUTO_DOWNLOAD"))
        self.auto_download_action.triggered.connect(
            lambda: utils.modifier_parametre_config("AUTO_DOWNLOAD", self.auto_download_action.isChecked()))
        parametres_menu.addAction(self.auto_download_action)
        self.remove_local_action = QtGui.QAction("Supprimer aussi les fichiers locaux lors de la suppréssion d'un élément", self)
        self.remove_local_action.setCheckable(True)
        self.remove_local_action.setChecked(config.getboolean("GLOBAL", "REMOVE_LOCAL"))
        self.remove_local_action.triggered.connect(
            lambda: utils.modifier_parametre_config("REMOVE_LOCAL", self.remove_local_action.isChecked()))
        parametres_menu.addAction(self.remove_local_action)
        # Menu Actions.
        actions_menu = menubar.addMenu("Actions")
        actions_config = QtGui.QAction("Configuration", self)
        actions_config.triggered.connect(self.config_parametres)
        actualiser_action = QtGui.QAction("Actualiser les éléments affichés", self)
        actualiser_action.triggered.connect(lambda: self.actualiser_affichage_thread())
        supprimer_tout_action = QtGui.QAction("Supprimer tous les éléments", self)
        supprimer_tout_action.triggered.connect(lambda: utils.supprimer_tout_elements(self, json_path))
        actions_menu.addAction(actions_config)
        actions_menu.addAction(actualiser_action)
        actions_menu.addAction(supprimer_tout_action)
        # Menu à propos.
        apropos_menu = menubar.addMenu("A propos")
        github_action = QtGui.QAction("Github", self)
        github_action.triggered.connect(lambda: webbrowser.open("https://github.com/Robin-mlh/Soundcloud-Sync"))
        apropos_menu.addAction(github_action)
        aide_action = QtGui.QAction("Aide", self)
        aide_action.triggered.connect(lambda: webbrowser.open("https://github.com/Robin-mlh/Soundcloud-Sync/tree/main?tab=readme-ov-file#param%C3%A8tres"))
        apropos_menu.addAction(aide_action)
        version_action = QtGui.QAction("Version", self)
        version_action.triggered.connect(lambda: utils.fenetre_info("Version", f"Version {utils.VERSION}", self))
        apropos_menu.addAction(version_action)

        # Barre de status en bas de la fenetre.
        self.barre_status = self.statusBar()
        self.label_compte = QtWidgets.QLabel()
        self.barre_status.addPermanentWidget(self.label_compte)
        self.label_nb_fichiers = QtWidgets.QLabel()
        self.barre_status.addPermanentWidget(QtWidgets.QWidget(), 1)
        self.label_actualisation = QtWidgets.QLabel()
        self.barre_status.addPermanentWidget(self.label_actualisation)
        self.barre_status.addPermanentWidget(QtWidgets.QWidget(), 1)
        self.barre_status.addPermanentWidget(self.label_nb_fichiers)

        self.actualiser_affichage_thread()


    def actualiser_affichage_thread(self):
        """ Déclencher le Thread d'actualisation de l'affichage. """

        if not self.actualisation_en_cours:
            self.label_actualisation.setText("Actualisation en cours...")
            self.actualisation_en_cours = True
            self.sync_thread = utils.ActualiserAffichage(self)
            self.sync_thread.finished.connect(self.fin_actualisation_affichage_thread)
            self.sync_thread.start()


    def fin_actualisation_affichage_thread(self):
        """ Fin du Thread d'actulisation de l'affichage. """

        self.actualisation_en_cours = False
        self.label_actualisation.setText("")


    def ajouter_lien(self):
        """ Ajouter un lien au fichier JSON et à l'interface s'il est valide. """

        url = self.input_url.text()
        if url:
            if not url.startswith("https://soundcloud.com/"):
                utils.fenetre_info("Erreur", "Le lien fourni est invalide.\n"
                                       "Incluez uniquement des playlistes, albums, musiques ou utilisateurs Soundcloud.\n"
                                       "Exemple de format: 'https://soundcloud.com/ak420-anarkotek'", self)
            else:
                json_content = utils.load_json_file(json_path)
                content = sc_object.resolve(url)
                if isinstance(content, soundcloud.Track):  # Le lien fourni est une musique.
                    titre = utils.remplacer_caract_spec(content.title)
                    if not [url, f"/Musiques/{titre}"] in json_content["musiques"]:
                        json_content["musiques"].append((url, f"/Musiques/{titre}"))
                elif isinstance(content, soundcloud.AlbumPlaylist):
                    titre = utils.remplacer_caract_spec(content.title)
                    if content.is_album:  # Le lien fourni est un album.
                        if not [url, f"/Albums/{titre}/"] in json_content["albums"]:
                            json_content["albums"].append((url, f"/Albums/{titre}/"))
                    else:  # Le lien fourni est une playliste.
                        if not [url, f"/Playlists/{titre}/"] in json_content["playlists"]:
                            json_content["playlists"].append((url, f"/Playlists/{titre}/"))
                elif isinstance(content, soundcloud.User):
                    titre = utils.remplacer_caract_spec(content.username)
                    if not [url, f"/Artistes/{content.username}/"] in json_content["artistes"]:
                        json_content["artistes"].append((url, f"/Artistes/{titre}/"))
                else:  # Le lien n'est ni une musique, ni un album, ni une playliste, ni un artiste.
                    utils.fenetre_info("Erreur", "Le lien fourni est invalide.\n"
                                           "Incluez uniquement des playlistes, albums, musiques ou utilisateurs Soundcloud.\n"
                                           "Exemple de format: 'https://soundcloud.com/ak420-anarkotek'", self)
                utils.write_json_file(json_path, json_content)  # Mettre à jour le fichier JSON.

            self.input_url.clear()  # Vider la barre d'input.
            utils.actualiser_interface(self)
            if self.auto_download_action.isChecked():
                numero_ligne = utils.trouver_ligne_url(self, url[8:])
                self.sync_element_menu(numero_ligne)


    def sync_all_bouton(self):
        """ Action du bouton pour synchroniser tous les éléments. """

        self.bouton_sync.setText("Synchronisation...")
        self.bouton_sync.setEnabled(False)
        self.sync_thread = sync_fonctions.SyncAllThread(self, json_path, sc_object)
        self.sync_thread.finished.connect(self.synchronisation_terminee)
        self.sync_thread.start()


    def synchronisation_terminee(self):
        """Réinitialise l'état du bouton après la synchronisation."""

        self.bouton_sync.setText("Tout Synchroniser")
        self.bouton_sync.setEnabled(True)
        self.actualiser_affichage_thread()

    def fenetre_config_fermee(self):
        """ La fenêtre de configuration a été fermée. """

        self.actualiser_affichage_thread()

    def config_parametres(self):
        """ Ouvre la fenetre de configuration importée. """

        if self.config_window and not self.config_window.isVisible():
            # Vérifier si la fenetre de configuration est ouverte,
            # mettre self.config_window à None si ce n'est pas le cas.
            self.config_window = None
        if not self.config_window:
            # Si la fenetre n'est pas ouverte, l'ouvrir.
            self.config_window = config_windows.ConfigApp()
            self.config_window.config_closed.connect(self.fenetre_config_fermee)
            self.config_window.show()
        else:  # Si la fenetre est deja ouverte, la mettre au premier plan.
            self.config_window.activateWindow()
            self.config_window.raise_()


    def menu_contextuel(self, position):
        """ Défini le menu contextuel (clique droit) sur la liste des éléments. """

        row = self.table_elements.currentRow()
        if row >= 0:
            menu = QtWidgets.QMenu(self)
            action_copier_url = QtGui.QAction("Copier l'URL", self)
            action_copier_url.triggered.connect(lambda: self.copier_element(row))
            action_supprimer_element = QtGui.QAction("Supprimer l'élément", self)
            action_supprimer_element.triggered.connect(lambda: utils.supprimer_element(self, row, json_path))
            action_synchroniser_element = QtGui.QAction("Synchroniser l'élément", self)
            action_synchroniser_element.triggered.connect(lambda: self.sync_element_menu(row))
            menu.addAction(action_supprimer_element)
            menu.addAction(action_synchroniser_element)
            menu.addAction(action_copier_url)
            menu.exec(self.table_elements.viewport().mapToGlobal(position))


    def copier_element(self, row):
        """ Copier l'URL de l'élément sélectionné. """

        url = self.table_elements.item(row, 1).text()
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(url)


    def sync_element_menu(self, row):
        """ Synchroniser uniquement l'élément sélectionné dans le menu contextuel. """

        json_element = ["https://" + self.table_elements.item(row, 1).text(),
                        self.table_elements.item(row, 0).text()]
        library_path = str(Path(json_path).parent)
        self.sync_thread = sync_fonctions.SyncElementThread(self, library_path, sc_object, json_element)
        self.sync_thread.start()


def main():
    global config
    global json_path
    global sc_object

    print("Chargement de l'application...")
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("QStatusBar::item { border: 0px solid black }; ")

    # Vérifier la connexion internet.
    try:
        requests.get("https://soundcloud.com", timeout=5)
    except:
        utils.fenetre_info("Erreur", "Soundcloud n'est pas joignable.\n"
                                     "Vérifiez votre connexion internet")
        sys.exit(app.exec())
    # Vérifier les paramètres (dans le fichier de configuration).
    json_path, sc_object = utils.verification_parametres()
    if not sc_object and not json_path:  # Si des paramètres sont invalides:
        utils.fenetre_info("Erreur", "Les paramètres sont manquants ou invalides.")
    elif not sc_object:
        utils.fenetre_info("Erreur", "Le Token d'authentification est invalide.")
    elif not json_path:
        utils.fenetre_info("Erreur", "Le répertoire de synchronisation est invalide.")
    if not json_path or not sc_object:
        # Ouvrir la fenetre de configuration.
        config_window = config_windows.ConfigApp()
        config_window.show()
        app.exec()

    # Récupérer les paramètres depuis le fichier de configuration.
    config, json_path, json_data, sc_object = utils.recuperer_parametres()
    # Créer les dossiers des catégories de contenu s'ils n'existe pas.
    tracks_path = Path(config["GLOBAL"]["LOCAL_PATH"]) / "Musiques"
    tracks_path.mkdir(parents=True, exist_ok=True)
    tracks_path = Path(config["GLOBAL"]["LOCAL_PATH"]) / "Albums"
    tracks_path.mkdir(parents=True, exist_ok=True)
    tracks_path = Path(config["GLOBAL"]["LOCAL_PATH"]) / "Playlists"
    tracks_path.mkdir(parents=True, exist_ok=True)
    tracks_path = Path(config["GLOBAL"]["LOCAL_PATH"]) / "Artistes"
    tracks_path.mkdir(parents=True, exist_ok=True)

    # Lancer la fenetre principale de Soundcloud Sync.
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
