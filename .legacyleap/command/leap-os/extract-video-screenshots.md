Trigger the **video-screenshot-extractor** agent to extract unique desktop-application screenshots from recorded videos.

Rules:

- Input videos are located in `leap-os/videos/`
- Supported video formats are `.mp4`, `.mov`, `.mkv`, and `.webm`
- Analyze each video first and suggest crop options that remove Google Meet chrome, invite/avatar tiles, black meeting margins, and the Windows taskbar
- Ask the user to choose the crop before extracting screenshots
- Output unique screenshots to `leap-os/screenshots/rough/[video-name]/`
- Mirror the same unique screenshots to `leap-os/screenshots/final/[video-name]/`
- Archive existing per-video output folders before reruns
- Process videos sequentially to avoid CPU and disk pressure
- Use local `ffmpeg`, `ffprobe`, and Python/Pillow only; do not install new dependencies unless the user explicitly approves
- On fresh machines, guide the user to install prerequisites with conda:
  `conda create -n legacyleap-video python=3.11 -y`
  `conda activate legacyleap-video`
  `conda install -c conda-forge ffmpeg pillow -y`
- Use `.legacyleap/scripts/leap-os/video-screenshot-extractor/run.sh` on Linux, macOS, WSL, or Git Bash
- Use `.legacyleap\scripts\leap-os\video-screenshot-extractor\run.ps1` on native Windows PowerShell
- If Windows blocks local PowerShell scripts, run with `powershell -ExecutionPolicy Bypass -File .\.legacyleap\scripts\leap-os\video-screenshot-extractor\run.ps1`
