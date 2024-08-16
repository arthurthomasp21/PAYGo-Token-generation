Ce dépôt permet de générer des tokens pour modules Pay As You Go (PAYGo). 

Un module (device) permet de verrouiller un appareil Victron équipé d'un port VE.Direct. 
Il est caractérisé par un code de démarrage (starting code) et une clé (key). 
On peut simuler le comportement d'un module grâce à la fonction DeviceSimulator du fichier simulator.
Ce module est capable de décrypter un token grâce à sa clé.

Pour générer des tokens, il faut un "server" qui ait connaissance du code de démarrage et de la clé du module. 
On peut le générer grâce à la fonction SingleDeviceServerSimulator du fichier simulator. 
Ce serveur peut générer différents types de tokens : à partir d'une durée, d'une date etc.

On trouvera des exemples d'utilisation dans le fichier main.ipynb 
