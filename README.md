# Graphene Layer Segmentation and Contrast Analysis (English)

This repository integrates the **experimental work** of obtaining graphene by micromechanical exfoliation and the **computational pipeline** for segmentation and optical analysis of graphene images on silicon substrates with oxide (Si/SiO₂).

---

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your_user/graphene-segmentation.git
   cd graphene-segmentation/graphene-segmentation
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # source .venv/bin/activate  # On Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🖥️ Running the Desktop Application

Launch the graphical interface (GUI) with:
```bash
python -m app.gui
```

## 📝 How does the app work?

At startup, the desktop app shows a **workspace selector** to choose one of these flows:

1. **Segmentation (optical contrast)**: Current functional flow for image segmentation and layer classification.
2. **Optical contrast simulation**: Base workspace created for future physical/optical simulation tools.
3. **Raman analysis**: Base workspace created for future Raman spectra preprocessing and analysis.

### Current implemented workflow (Segmentation)

1. **Image upload**: Select an optical microscopy image (JPG, PNG).
2. **Preprocessing**: The green channel is extracted and filtered to enhance contrast.
3. **ROI selection**: The user manually selects a region of interest (ROI) on the image.
4. **Segmentation**: Multi-Otsu segmentation is applied to separate areas with different numbers of layers.
5. **Classification**: The contrast of each segmented area is analyzed to estimate the number of graphene layers.
6. **Visualization**: Results and graphical overlays are shown for interpretation.

## 📦 Project Structure

- `app/` Main source code
   - `gui.py` Main application shell and workspace selector (PySide6)
   - `modules/` UI workspaces
      - `segmentation_workspace.py` Functional segmentation workspace
      - `optical_simulation_workspace.py` Base workspace for optical simulation
      - `raman_workspace.py` Base workspace for Raman analysis
   - `pipeline/` Modules for loading, preprocessing, segmentation, analysis, and visualization
- `assets/` Example images and resources
- `colab-pipeline/` Notebook for Google Colab experiments
- `tests/` Automated tests (if applicable)

## 📄 Additional Contents

- **Experimental Paper**:  
  *Preliminary Production and Characterization of Graphene on Silicon Substrates via Micromechanical Exfoliation*  
  Juan Pablo González Blandón, Juan José Balvin Torres (2025).

---

For questions or contributions, open an issue or pull request.