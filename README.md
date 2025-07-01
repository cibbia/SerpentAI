![](https://s3.ca-central-1.amazonaws.com/serpent-ai-assets/SerpentFBCover.png)

# Serpent.AI - Game Agent Framework (Python)

[![](https://img.shields.io/badge/project-website-brightgreen.svg?colorB=1bcc6f&longCache=true)](http://serpent.ai)
[![](https://img.shields.io/badge/project-blog-brightgreen.svg?colorB=1bcc6f&longCache=true)](http://blog.serpent.ai)
[![](https://img.shields.io/badge/project-wiki-brightgreen.svg?colorB=1bcc6f&longCache=true)](https://github.com/SerpentAI/SerpentAI/wiki)    
[![](https://img.shields.io/badge/pypi-v2018.1.2-brightgreen.svg?colorB=007ec6&longCache=true)]()
[![](https://img.shields.io/badge/python-3.6-brightgreen.svg?colorB=007ec6&longCache=true)]()
[![](https://img.shields.io/badge/license-MIT-brightgreen.svg?colorB=007ec6&longCache=true)]()  
[![](https://img.shields.io/badge/twitter-@Serpent__AI-brightgreen.svg?colorB=1da1f2&longCache=true)](https://twitter.com/Serpent_AI)

## Update: Revival (May 2020)

Development work has resumed on the framework with the aim of bringing it into 2020: Python 3.8+, Less Dependencies, Ease of Use (Installer, GUI) and much more! Still open-source with a permissive license and looking into a Steam distribution for non-technical users. 🐍

## ~~Warning: End of life (November 2018)~~

Serpent.AI is a simple yet powerful, novel framework to assist developers in the creation of game agents. Turn ANY video game you own  into a sandbox environment ripe for experimentation, all with familiar Python code. The framework's _raison d'être_ is first and foremost to provide a valuable tool for Machine Learning & AI research. It also turns out to be ridiculously fun to use as a hobbyist (and dangerously addictive; a fair warning)!

The framework features a large assortment of supporting modules that provide solutions to commonly encountered scenarios when using video games as environments  as well as CLI tools to accelerate development. It provides some useful conventions but is absolutely NOT opiniated about what you put in your agents: Want to use the latest, cutting-edge deep reinforcement learning algorithm? ALLOWED. Want to use computer vision techniques, image processing and trigonometry? ALLOWED. Want to randomly press the Left or Right buttons? _sigh_ ALLOWED. To top it all off, Serpent.AI was designed to be entirely plugin-based (for both game support and game agents) so your experiments are actually portable and distributable to your peers and random strangers on the Internet.

Serpent.AI supports Linux, Windows ~~& macOS~~.

_The next version of the framework will officially stop supporting macOS. Apple's aversion to Nvidia in their products means no recent macOS machine can run CUDA, an essential piece of technology for Serpent.AI's real-time training. Other decisions like preventing 32-bit applications from running in Catalina and deprecating OpenGL do not help make a case to support the OS._ 

![](https://s3.ca-central-1.amazonaws.com/serpent-ai-assets/demo_isaac.gif)

_Experiment: Game agent learning to defeat Monstro (The Binding of Isaac: Afterbirth+)_

## Background

The project was born out of admiration for / frustration with [OpenAI Universe](https://github.com/openai/universe). The idea is perfect, let's be honest, but some implementation details leave a lot to be desired. From these, the core tennets of the framework were established:

1. Thou shall run natively. Thou shalt not use Docker containers or VNC servers.
2. Thou shall allow a user to bring their own games. Thou shalt not wait for licensing deals and special game APIs.
3. Thou shall encourage diverse and creative approaches. Thou shalt not only enable AI flavors of the month.

_Want to know more about how Serpent.AI came to be? Read [The Story Behind Serpent.AI](http://blog.serpent.ai/the-story-behind-serpent-ai/) on the blog!_

## Documentation

Guides, tutorials and videos are being produced and added to the [GitHub Wiki](https://github.com/SerpentAI/SerpentAI/wiki). It currently is the official source of documentation.

![](https://s3.ca-central-1.amazonaws.com/serpent-ai-assets/demo_ymbab.gif)

_Experiment: Game agent learning to match tiles (You Must Build a Boat)_

_Business Contact: info@serpent.ai_

## Installation (2025 refresh)

Serpent.AI now ships with **two install flavours**.

1. **Minimal** – Installs only the lightweight core and CLI (suitable for dev/CI and unit-testing).  _Default._
   ```bash
   pip install serpentai  # or `poetry add serpentai`
   ```

2. **Full** – Pulls in the complete scientific/ML stack (PyTorch, TensorFlow, scikit-image, etc.) required for training agents and computer-vision heavy workflows.
   ```bash
   pip install serpentai[full]
   ```

>  ⚠  The first install is ~10 MB, the full one can exceed 2 GB including CUDA wheels – choose wisely!

### Python compatibility

• CPython 3.8 → 3.13.
• Linux & Windows officially supported. macOS may work but GPU training is **not** supported.

### Reinforcement-Learning with Stable-Baselines3

The `[full]` install now includes **Stable-Baselines3** and **Gymnasium**.

```bash
pip install serpentai[full]

python -m serpent.examples.train_sb3  # coming soon
```

This will let you train PPO/A2C/DQN agents on your favourite games with just a few lines of code.

## Experiment tracking with TensorBoard

Serpent now writes training metrics to `runs/` (PyTorch standard).  View them with either:

```bash
serpent tensorboard         # opens browser at http://localhost:6006
```

or click **TensorBoard → Open** in the Streamlit sidebar.

## AppImage auto-update

The generated AppImage embeds *update information* so you can delta-update in place:

```bash
./SerpentAI-*.AppImage --appimage-update
```

or download [AppImageUpdate](https://github.com/AppImage/AppImageUpdate) and just double-click.
