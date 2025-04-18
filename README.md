# Albert Conversation 👋

![GitHub stars](https://img.shields.io/github/stars/etalab-ia/albert-conversation?style=social)
![GitHub forks](https://img.shields.io/github/forks/etalab-ia/albert-conversation?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/etalab-ia/albert-conversation?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/etalab-ia/albert-conversation)
![GitHub language count](https://img.shields.io/github/languages/count/etalab-ia/albert-conversation)
![GitHub top language](https://img.shields.io/github/languages/top/etalab-ia/albert-conversation)
![GitHub last commit](https://img.shields.io/github/last-commit/etalab-ia/albert-conversation?color=red)

**Albert Conversation est un fork de [Open WebUI](https://github.com/open-webui/open-webui), une plateforme IA auto-hébergée, [extensible](https://docs.openwebui.com/features/plugin/), riche en fonctionnalités et facile à utiliser, conçue pour fonctionner entièrement hors ligne.** Elle prend en charge divers moteurs LLM comme **Ollama** et les API compatibles **OpenAI** telles que [Albert API](https://github.com/etalab-ia/albert-api), avec un **moteur d'inférence intégré** pour le RAG, en faisant une **solution puissante de déploiement d'IA**.

![Démo Albert Conversation](./demo.gif)

## Fonctionnalités Clés ⭐

- 🚀 **Installation Facile** : Installation simple avec Docker ou Kubernetes (kubectl, kustomize ou helm) avec prise en charge des images `:ollama` et `:cuda`.

- 🤝 **Intégration API Ollama/OpenAI** : Intégrez facilement des API compatibles OpenAI et des modèles Ollama. Personnalisez l'URL de l'API pour vous connecter à **LMStudio, GroqCloud, Mistral, OpenRouter, et plus encore**.

- 🛡️ **Permissions Granulaires et Groupes d'Utilisateurs** : Créez des rôles détaillés pour plus de sécurité et une expérience utilisateur personnalisée.

- 📱 **Design Responsive** : Utilisable sur PC, portable et mobile.

- 📱 **PWA pour Mobile** : Expérience similaire à une application native, avec accès hors ligne sur localhost.

- ✒️🔢 **Support Complet Markdown et LaTeX** : Expérience LLM enrichie avec Markdown et LaTeX.

- 🎤📹 **Appels Audio/Vidéo Mains Libres** : Discussions dynamiques avec appels intégrés.

- 🛠️ **Créateur de Modèles** : Créez des modèles Ollama, personnages/agents personnalisés, éléments de chat, et importation facile via la [Communauté Albert](https://openwebui.com/).

- 🐍 **Appel de Fonctions Python Natives** : Ajoutez vos fonctions Python dans l'éditeur de code intégré pour une intégration fluide.

- 📚 **RAG Local Intégré** : Chargez des documents dans la discussion ou dans la bibliothèque, accessibles via la commande `#`.

- 🔍 **Recherche Web pour RAG** : Effectuez des recherches via `SearXNG`, `Google PSE`, `Brave`, `serpstack`, `DuckDuckGo`, `Tavily`, `Bing`, etc.

- 🌐 **Navigation Web** : Intégrez des sites dans vos discussions via la commande `#` suivie d'une URL.

- 🎨 **Génération d'Images** : Génération d'images via AUTOMATIC1111 API, ComfyUI, ou DALL-E.

- ⚙️ **Conversations Multi-Modèles** : Utilisez plusieurs modèles simultanément pour des réponses optimales.

- 🔐 **Contrôle d'Accès par Rôles (RBAC)** : Droits d'accès restreints selon les rôles d'utilisateur.

- 🌐🌍 **Support Multilingue** : Interface traduisible avec support i18n. Contributeurs bienvenus !

- 🧩 **Pipelines et Plugins** : Ajoutez de la logique personnalisée avec [Pipelines](https://github.com/open-webui/pipelines). Exemples : **Appel de fonction**, **Limitations d'accès**, **Traduction en direct**, **Filtrage de messages toxiques**, etc.

- 🌟 **Mises à Jour Régulières** : Nous publions fréquemment des améliorations et corrections.

## Installation 🚀

### Démarrage Rapide avec Docker 🐳

Commencez par construire l'image Docker locale :

```bash
docker build -t albert-conversation .
```

> [!NOTE]  
> Des configurations supplémentaires peuvent être nécessaires dans certains environnements Docker. Consultez la [Documentation](https://docs.openwebui.com/).

> [!WARNING]  
> Ajoutez `-v albert-conversation:/app/backend/data` à votre commande Docker pour éviter toute perte de données.

> [!TIP]  
> Pour utiliser Albert Conversation avec Ollama ou l'accélération CUDA, nous recommandons de construire avec les arguments appropriés : `--build-arg="USE_CUDA=true"` ou `--build-arg="USE_OLLAMA=true"`. Pour activer CUDA, vous devez installer l'[outil Nvidia CUDA pour conteneurs](https://docs.nvidia.com/dgx/nvidia-container-runtime-upgrade/).

### Installation avec Configuration par Défaut

- **Si Ollama est sur votre machine** :

  ```bash
  docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation
  ```

- **Si Ollama est sur un autre serveur** :

  Pour vous connecter à Ollama sur un autre serveur, modifiez `OLLAMA_BASE_URL` avec l'URL du serveur :

  ```bash
  docker run -d -p 3000:8080 -e OLLAMA_BASE_URL=https://example.com -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation
  ```

- **Pour exécuter Albert Conversation avec accélération GPU Nvidia**, construisez d'abord avec le support CUDA :

  ```bash
  docker build -t albert-conversation:cuda --build-arg="USE_CUDA=true" .
  ```

  Puis exécutez avec le support GPU :

  ```bash
  docker run -d -p 3000:8080 --gpus all --add-host=host.docker.internal:host-gateway -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation:cuda
  ```

### Installation pour l'utilisation de l'API OpenAI uniquement

- **Si vous utilisez uniquement l'API OpenAI** :

  ```bash
  docker run -d -p 3000:8080 -e OPENAI_API_KEY=your_secret_key -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation
  ```

### Installation d'Albert Conversation avec Support Ollama Intégré

Cette méthode d'installation utilise une image conteneur unique qui intègre Albert Conversation avec Ollama. Commencez par construire l'image avec le support Ollama :

```bash
docker build -t albert-conversation:ollama --build-arg="USE_OLLAMA=true" .
```

Choisissez la commande appropriée selon votre configuration matérielle :

- **Avec Support GPU** :
  Utilisez les ressources GPU en exécutant la commande suivante :

  ```bash
  docker run -d -p 3000:8080 --gpus=all -v ollama:/root/.ollama -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation:ollama
  ```

- **Pour CPU Uniquement** :
  Si vous n'utilisez pas de GPU, utilisez plutôt cette commande :

  ```bash
  docker run -d -p 3000:8080 -v ollama:/root/.ollama -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation:ollama
  ```

Les deux commandes facilitent une installation sans tracas d'Albert Conversation et d'Ollama, garantissant que vous pouvez tout faire fonctionner rapidement.

Après l'installation, vous pouvez accéder à Albert Conversation à l'adresse [http://localhost:3000](http://localhost:3000). Profitez-en ! 😄

### Autres Méthodes d'Installation

Nous proposons diverses alternatives d'installation, y compris des méthodes d'installation natives non-Docker, Docker Compose, Kustomize et Helm. Visitez notre [Documentation](https://docs.openwebui.com/getting-started/).

### Dépannage

Des problèmes de connexion ? Notre [Documentation](https://docs.openwebui.com/troubleshooting/) est là pour vous aider.

#### Albert Conversation : Erreur de Connexion au Serveur

Si vous rencontrez des problèmes de connexion, c'est souvent dû au fait que le conteneur docker ne peut pas atteindre le serveur Ollama à 127.0.0.1:11434 (host.docker.internal:11434) à l'intérieur du conteneur. Utilisez l'option `--network=host` dans votre commande docker pour résoudre ce problème. Notez que le port change de 3000 à 8080, donnant le lien : `http://localhost:8080`.

**Exemple de Commande Docker** :

```bash
docker run -d --network=host -v albert-conversation:/app/backend/data -e OLLAMA_BASE_URL=http://127.0.0.1:11434 --name albert-conversation --restart always albert-conversation
```

### Maintenir Votre Installation Docker à Jour

Pour mettre à jour votre installation Docker locale, vous devrez reconstruire l'image avec le code le plus récent :

```bash
git pull  # Obtenir le code le plus récent
docker build -t albert-conversation .  # Reconstruire l'image
docker stop albert-conversation  # Arrêter le conteneur en cours
docker rm albert-conversation   # Supprimer l'ancien conteneur
# Puis exécutez la commande docker run appropriée ci-dessus pour démarrer un nouveau conteneur
```

### Utilisation de la Branche Dev 🌙

> [!WARNING]
> La branche dev contient les dernières fonctionnalités instables et les changements. Utilisez-la à vos risques et périls car elle peut contenir des bugs ou des fonctionnalités incomplètes.

Si vous souhaitez essayer les dernières fonctionnalités de pointe et acceptez une instabilité occasionnelle, vous pouvez construire depuis la branche dev :

```bash
git checkout dev
docker build -t albert-conversation:dev .
docker run -d -p 3000:8080 -v albert-conversation:/app/backend/data --name albert-conversation --add-host=host.docker.internal:host-gateway --restart always albert-conversation:dev
```

### Offline Mode

Pour empêcher les téléchargements :

```bash
export HF_HUB_OFFLINE=1
```

## License 📜

Ce projet est sous licence BSD-3-Clause License - voir le fichier LICENSE pour plus de détails. 📄

### Support 💬

Des questions ? Suggestions ? Besoin d'aide ? Contactez-nous à : contact-albert@numerique.gouv.fr

---
Open WebUI a été créé par [Timothy Jaeryang Baek](https://github.com/tjbck)


**Albert Conversation is a fork of [Open WebUI](https://github.com/open-webui/open-webui) an [extensible](https://docs.openwebui.com/features/plugin/), feature-rich, and user-friendly self-hosted AI platform designed to operate entirely offline.** It supports various LLM runners like **Ollama** and **OpenAI-compatible APIs** like [Albert API](https://github.com/etalab-ia/albert-api), with **built-in inference engine** for RAG, making it a **powerful AI deployment solution**.

![Albert Conversation Demo](./demo.gif)

## Key Features ⭐

- 🚀 **Effortless Setup**: Install seamlessly using Docker or Kubernetes (kubectl, kustomize or helm) for a hassle-free experience with support for both `:ollama` and `:cuda` tagged images.

- 🤝 **Ollama/OpenAI API Integration**: Effortlessly integrate OpenAI-compatible APIs for versatile conversations alongside Ollama models. Customize the OpenAI API URL to link with **LMStudio, GroqCloud, Mistral, OpenRouter, and more**.

- 🛡️ **Granular Permissions and User Groups**: By allowing administrators to create detailed user roles and permissions, we ensure a secure user environment. This granularity not only enhances security but also allows for customized user experiences, fostering a sense of ownership and responsibility amongst users.

- 📱 **Responsive Design**: Enjoy a seamless experience across Desktop PC, Laptop, and Mobile devices.

- 📱 **Progressive Web App (PWA) for Mobile**: Enjoy a native app-like experience on your mobile device with our PWA, providing offline access on localhost and a seamless user interface.

- ✒️🔢 **Full Markdown and LaTeX Support**: Elevate your LLM experience with comprehensive Markdown and LaTeX capabilities for enriched interaction.

- 🎤📹 **Hands-Free Voice/Video Call**: Experience seamless communication with integrated hands-free voice and video call features, allowing for a more dynamic and interactive chat environment.

- 🛠️ **Model Builder**: Easily create Ollama models via the Web UI. Create and add custom characters/agents, customize chat elements, and import models effortlessly through [Albert Conversation Community](https://openwebui.com/) integration.

- 🐍 **Native Python Function Calling Tool**: Enhance your LLMs with built-in code editor support in the tools workspace. Bring Your Own Function (BYOF) by simply adding your pure Python functions, enabling seamless integration with LLMs.

- 📚 **Local RAG Integration**: Dive into the future of chat interactions with groundbreaking Retrieval Augmented Generation (RAG) support. This feature seamlessly integrates document interactions into your chat experience. You can load documents directly into the chat or add files to your document library, effortlessly accessing them using the `#` command before a query.

- 🔍 **Web Search for RAG**: Perform web searches using providers like `SearXNG`, `Google PSE`, `Brave Search`, `serpstack`, `serper`, `Serply`, `DuckDuckGo`, `TavilySearch`, `SearchApi` and `Bing` and inject the results directly into your chat experience.

- 🌐 **Web Browsing Capability**: Seamlessly integrate websites into your chat experience using the `#` command followed by a URL. This feature allows you to incorporate web content directly into your conversations, enhancing the richness and depth of your interactions.

- 🎨 **Image Generation Integration**: Seamlessly incorporate image generation capabilities using options such as AUTOMATIC1111 API or ComfyUI (local), and OpenAI's DALL-E (external), enriching your chat experience with dynamic visual content.

- ⚙️ **Many Models Conversations**: Effortlessly engage with various models simultaneously, harnessing their unique strengths for optimal responses. Enhance your experience by leveraging a diverse set of models in parallel.

- 🔐 **Role-Based Access Control (RBAC)**: Ensure secure access with restricted permissions; only authorized individuals can access your Ollama, and exclusive model creation/pulling rights are reserved for administrators.

- 🌐🌍 **Multilingual Support**: Experience Albert Conversation in your preferred language with our internationalization (i18n) support. Join us in expanding our supported languages! We're actively seeking contributors!

- 🧩 **Pipelines, Albert Conversation Plugin Support**: Seamlessly integrate custom logic and Python libraries into Albert Conversation using [Pipelines Plugin Framework](https://github.com/open-webui/pipelines). Launch your Pipelines instance, set the OpenAI URL to the Pipelines URL, and explore endless possibilities. [Examples](https://github.com/open-webui/pipelines/tree/main/examples) include **Function Calling**, User **Rate Limiting** to control access, **Usage Monitoring** with tools like Langfuse, **Live Translation with LibreTranslate** for multilingual support, **Toxic Message Filtering** and much more.

- 🌟 **Continuous Updates**: We are committed to improving Albert Conversation with regular updates, fixes, and new features.

## How to Install 🚀

### Quick Start with Docker 🐳

First, build the local Docker image:

```bash
docker build -t albert-conversation .
```

> [!NOTE]  
> Please note that for certain Docker environments, additional configurations might be needed. If you encounter any connection issues, our detailed guide on [the Documentation](https://docs.openwebui.com/) is ready to assist you.

> [!WARNING]
> When using Docker to install Albert Conversation, make sure to include the `-v albert-conversation:/app/backend/data` in your Docker command. This step is crucial as it ensures your database is properly mounted and prevents any loss of data.

> [!TIP]  
> If you wish to utilize Albert Conversation with Ollama included or CUDA acceleration, we recommend building with the appropriate build args: `--build-arg="USE_CUDA=true"` or `--build-arg="USE_OLLAMA=true"`. To enable CUDA, you must install the [Nvidia CUDA container toolkit](https://docs.nvidia.com/dgx/nvidia-container-runtime-upgrade/) on your Linux/WSL system.

### Installation with Default Configuration

- **If Ollama is on your computer**, use this command:

  ```bash
  docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation
  ```

- **If Ollama is on a Different Server**, use this command:

  To connect to Ollama on another server, change the `OLLAMA_BASE_URL` to the server's URL:

  ```bash
  docker run -d -p 3000:8080 -e OLLAMA_BASE_URL=https://example.com -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation
  ```

- **To run Albert Conversation with Nvidia GPU support**, first build with CUDA support:

  ```bash
  docker build -t albert-conversation:cuda --build-arg="USE_CUDA=true" .
  ```

  Then run with GPU support:

  ```bash
  docker run -d -p 3000:8080 --gpus all --add-host=host.docker.internal:host-gateway -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation:cuda
  ```

### Installation for OpenAI API Usage Only

- **If you're only using OpenAI API**, use this command:

  ```bash
  docker run -d -p 3000:8080 -e OPENAI_API_KEY=your_secret_key -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation
  ```

### Installing Albert Conversation with Bundled Ollama Support

This installation method uses a single container image that bundles Albert Conversation with Ollama. First, build the image with Ollama support:

```bash
docker build -t albert-conversation:ollama --build-arg="USE_OLLAMA=true" .
```

Choose the appropriate command based on your hardware setup:

- **With GPU Support**:
  Utilize GPU resources by running the following command:

  ```bash
  docker run -d -p 3000:8080 --gpus=all -v ollama:/root/.ollama -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation:ollama
  ```

- **For CPU Only**:
  If you're not using a GPU, use this command instead:

  ```bash
  docker run -d -p 3000:8080 -v ollama:/root/.ollama -v albert-conversation:/app/backend/data --name albert-conversation --restart always albert-conversation:ollama
  ```

Both commands facilitate a built-in, hassle-free installation of both Albert Conversation and Ollama, ensuring that you can get everything up and running swiftly.

After installation, you can access Albert Conversation at [http://localhost:3000](http://localhost:3000). Enjoy! 😄

### Other Installation Methods

We offer various installation alternatives, including non-Docker native installation methods, Docker Compose, Kustomize, and Helm. Visit our [Documentation](https://docs.openwebui.com/getting-started/).

### Troubleshooting

Encountering connection issues? Our [Documentation](https://docs.openwebui.com/troubleshooting/) has got you covered.

#### Albert Conversation: Server Connection Error

If you're experiencing connection issues, it's often due to the docker container not being able to reach the Ollama server at 127.0.0.1:11434 (host.docker.internal:11434) inside the container . Use the `--network=host` flag in your docker command to resolve this. Note that the port changes from 3000 to 8080, resulting in the link: `http://localhost:8080`.

**Example Docker Command**:

```bash
docker run -d --network=host -v albert-conversation:/app/backend/data -e OLLAMA_BASE_URL=http://127.0.0.1:11434 --name albert-conversation --restart always albert-conversation
```

### Keeping Your Docker Installation Up-to-Date

To update your local Docker installation, you'll need to rebuild the image with the latest code:

```bash
git pull  # Get the latest code
docker build -t albert-conversation .  # Rebuild the image
docker stop albert-conversation  # Stop the running container
docker rm albert-conversation   # Remove the old container
# Then run the appropriate docker run command from above to start a new container
```

### Using the Dev Branch 🌙

> [!WARNING]
> The dev branch contains the latest unstable features and changes. Use it at your own risk as it may have bugs or incomplete features.

If you want to try out the latest bleeding-edge features and are okay with occasional instability, you can build from the dev branch:

```bash
git checkout dev
docker build -t albert-conversation:dev .
docker run -d -p 3000:8080 -v albert-conversation:/app/backend/data --name albert-conversation --add-host=host.docker.internal:host-gateway --restart always albert-conversation:dev
```

### Offline Mode

If you are running Albert Conversation in an offline environment, you can set the `HF_HUB_OFFLINE` environment variable to `1` to prevent attempts to download models from the internet.

```bash
export HF_HUB_OFFLINE=1
```

## License 📜

This project is licensed under the [BSD-3-Clause License](LICENSE) - see the [LICENSE](LICENSE) file for details. 📄

## Support 💬

If you have any questions, suggestions, or need assistance, please contact us at contact-albert@numerique.gouv.fr

---

Open WebUI was created by [Timothy Jaeryang Baek](https://github.com/tjbck)