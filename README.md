# Fluffy Terminators FLL 

### Development within Visual Studio Code

Install [this extension](https://marketplace.visualstudio.com/items?itemName=PeterStaev.lego-spikeprime-mindstorms-vscode) to allow direct uploading to the Hub via VS Code.
And if you add a `# LEGO slot:7 autostart` comment to the start of your python file,
you can specify which slot to use for that file, and allow auto-starting the script after
upload completes (for some reason `slot:0` doesn't seem to work well with autostart?!).

Stubs in `./spike_stubs/` (plus `./vscode/settings.json`) prevent complaints about import
errors but also serve to provide autocompletion and documentation within the IDE.
