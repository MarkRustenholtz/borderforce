/*
 * BorderForce — horaires SNCF théoriques hors connexion
 * Secteur Roya : Breil-sur-Roya, Fontan-Saorge, Saint-Dalmas-de-Tende,
 * La Brigue et Tende.
 *
 * Les données de l’API SNCF restent toujours prioritaires dès qu’une
 * connexion Internet est disponible.
 */
window.BF_SNCF_ROYA_DATA = {
  "schemaVersion": 3,
  "version": "2026-08-02",
  "gares": [
    "Breil-sur-Roya",
    "Fontan-Saorge",
    "Saint-Dalmas-de-Tende",
    "La Brigue",
    "Tende"
  ],
  "garesUIC": {
    "Breil-sur-Roya": "87756833",
    "Fontan-Saorge": "87756858",
    "Saint-Dalmas-de-Tende": "87756866",
    "La Brigue": "87756874",
    "Tende": "87756882"
  },
  "operateur": "SNCF Voyageurs / ZOU !",
  "typeDonnees": "horaires_theoriques",
  "validiteDu": "2026-08-02",
  "validiteAu": "2026-12-12",
  "source": {
    "nom": "Horaires théoriques SNCF — ligne 05 Nice–Breil-sur-Roya–Tende",
    "jeuDeDonnees": "GTFS SNCF Voyageurs et fiche horaire officielle TER ZOU !",
    "dateExtraction": "2026-08-02",
    "note": "Fichier local de secours hors connexion. Les données en ligne de l’API SNCF restent prioritaires. Les adaptations de desserte, travaux, suppressions et retards ne peuvent pas être connus hors connexion."
  },
  "couverture": {
    "description": "Trains SNCF réguliers desservant au moins une des cinq gares. Les services routiers ZOU ! et les renforts saisonniers non garantis ne sont pas inclus.",
    "nombreTrains": 23
  },
  "circulationParDefaut": {
    "joursSemaine": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ],
    "joursFeries": true,
    "exclusions": [],
    "inclusions": [],
    "libelle": "Horaire théorique local de secours — vérifier les adaptations et perturbations le jour du service."
  },
  "trains": [
    {
      "numero": "881303",
      "origine": "Nice",
      "destination": "Breil-sur-Roya",
      "arriveeBreil": "06:40"
    },
    {
      "numero": "881305",
      "origine": "Nice",
      "destination": "Breil-sur-Roya",
      "arriveeBreil": "07:40"
    },
    {
      "numero": "881307",
      "origine": "Nice",
      "destination": "Breil-sur-Roya",
      "arriveeBreil": "08:46"
    },
    {
      "numero": "881309",
      "origine": "Nice",
      "destination": "Breil-sur-Roya",
      "arriveeBreil": "09:41"
    },
    {
      "numero": "22991",
      "origine": "Nice",
      "destination": "Tende",
      "arriveeBreil": "10:42",
      "departBreil": "10:44",
      "arriveeFontanSaorge": "10:55",
      "departFontanSaorge": "10:55",
      "arriveeSaintDalmasTende": "11:17",
      "departSaintDalmasTende": "11:17",
      "arriveeLaBrigue": "11:24",
      "departLaBrigue": "11:24",
      "arriveeTende": "11:32"
    },
    {
      "numero": "22993",
      "origine": "Nice",
      "destination": "Tende",
      "arriveeBreil": "12:39",
      "departBreil": "12:41",
      "arriveeFontanSaorge": "12:52",
      "departFontanSaorge": "12:52",
      "arriveeSaintDalmasTende": "13:13",
      "departSaintDalmasTende": "13:13",
      "arriveeLaBrigue": "13:21",
      "departLaBrigue": "13:21",
      "arriveeTende": "13:28"
    },
    {
      "numero": "22995",
      "origine": "Nice",
      "destination": "Tende",
      "arriveeBreil": "14:42",
      "departBreil": "14:45",
      "arriveeFontanSaorge": "14:56",
      "departFontanSaorge": "14:56",
      "arriveeSaintDalmasTende": "15:17",
      "departSaintDalmasTende": "15:17",
      "arriveeLaBrigue": "15:26",
      "departLaBrigue": "15:26",
      "arriveeTende": "15:34"
    },
    {
      "numero": "881325",
      "origine": "Nice",
      "destination": "Breil-sur-Roya",
      "arriveeBreil": "17:40"
    },
    {
      "numero": "881327",
      "origine": "Nice",
      "destination": "Breil-sur-Roya",
      "arriveeBreil": "18:40"
    },
    {
      "numero": "881329",
      "origine": "Nice",
      "destination": "Breil-sur-Roya",
      "arriveeBreil": "19:36"
    },
    {
      "numero": "881331",
      "origine": "Nice",
      "destination": "Breil-sur-Roya",
      "arriveeBreil": "20:40"
    },
    {
      "numero": "881304",
      "origine": "Breil-sur-Roya",
      "destination": "Nice",
      "departBreil": "05:49"
    },
    {
      "numero": "881308",
      "origine": "Breil-sur-Roya",
      "destination": "Nice",
      "departBreil": "06:45"
    },
    {
      "numero": "881310",
      "origine": "Breil-sur-Roya",
      "destination": "Nice",
      "departBreil": "07:49"
    },
    {
      "numero": "881312",
      "origine": "Breil-sur-Roya",
      "destination": "Nice",
      "departBreil": "08:50"
    },
    {
      "numero": "881314",
      "origine": "Breil-sur-Roya",
      "destination": "Nice",
      "departBreil": "09:49"
    },
    {
      "numero": "881318",
      "origine": "Breil-sur-Roya",
      "destination": "Nice",
      "departBreil": "11:48"
    },
    {
      "numero": "22984",
      "origine": "Tende",
      "destination": "Nice",
      "departTende": "12:59",
      "arriveeLaBrigue": "13:05",
      "departLaBrigue": "13:05",
      "arriveeSaintDalmasTende": "13:12",
      "departSaintDalmasTende": "13:12",
      "arriveeFontanSaorge": "13:34",
      "departFontanSaorge": "13:34",
      "arriveeBreil": "13:47",
      "departBreil": "13:51"
    },
    {
      "numero": "22986",
      "origine": "Tende",
      "destination": "Nice",
      "departTende": "15:02",
      "arriveeLaBrigue": "15:08",
      "departLaBrigue": "15:08",
      "arriveeSaintDalmasTende": "15:15",
      "departSaintDalmasTende": "15:15",
      "arriveeFontanSaorge": "15:40",
      "departFontanSaorge": "15:40",
      "arriveeBreil": "15:53",
      "departBreil": "15:56"
    },
    {
      "numero": "22988",
      "origine": "Tende",
      "destination": "Breil-sur-Roya",
      "departTende": "16:38",
      "arriveeLaBrigue": "16:44",
      "departLaBrigue": "16:44",
      "arriveeSaintDalmasTende": "16:51",
      "departSaintDalmasTende": "16:51",
      "arriveeFontanSaorge": "17:13",
      "departFontanSaorge": "17:13",
      "arriveeBreil": "17:27"
    },
    {
      "numero": "881330",
      "origine": "Breil-sur-Roya",
      "destination": "Nice",
      "departBreil": "17:49"
    },
    {
      "numero": "881334",
      "origine": "Breil-sur-Roya",
      "destination": "Nice",
      "departBreil": "19:48"
    },
    {
      "numero": "881336",
      "origine": "Breil-sur-Roya",
      "destination": "Nice",
      "departBreil": "20:50"
    }
  ],
  "sourceLocale": "Fichier SNCF"
};
