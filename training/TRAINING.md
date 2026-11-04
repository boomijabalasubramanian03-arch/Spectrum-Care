# Training your own fruit-detection model

> **Status:** the dataset is validated and ready (510 images / 1,000+ boxes, 0 broken
> labels - checked), but **the model has NOT been trained yet** - there is no
> `custom_fruit.pt` in the project. Training needs a GPU and internet, so it must
> be run by you in Colab (or with `python train_local.py`). Until you do, the app
> uses the pretrained COCO model, which works fully offline. If you set
> `USE_CUSTOM_MODEL=1` without the file, the app now falls back to COCO instead of crashing.

Your project currently identifies objects using a model that was pretrained
by someone else (see the main README). This folder lets you train your
own instead, on a real, labelled dataset — 510 photos across 6 fruit
classes (Apple, Banana, Grape, Orange, Pineapple, Watermelon), taken from a
public dataset annotated with the Roboflow tool.

## Why a subset, and why fruit specifically
The full dataset has ~8,500 images — too slow to train on for a class demo
and too big to hand you as a zip. This is a balanced 510-image slice (70
per class for training, 15 per class for checking accuracy). Fruit was
picked because it's exactly the "Red Apple" example your own spec uses
throughout.

**Trade-off to know:** the pretrained model you have now recognises 80
everyday object types (people, cars, dogs, chairs...). A model trained only
on this dataset will recognise **just the 6 fruit classes** — it won't see
a person or a car at all. That's normal for a custom-trained model with a
small, focused dataset. If you want both, see "Going further" below.

## Steps

1. **Train it.** Open `train_custom_model.ipynb` in Google Colab
   (upload it at https://colab.research.google.com, or open it from Google
   Drive). Turn on the free GPU (`Runtime > Change runtime type > T4 GPU`).
   Run every cell top to bottom. When asked, upload `dataset.zip`
   (zip the `dataset/` folder yourself first).
   Takes about 10–15 minutes.

2. **Download the result.** The last cell downloads `best.pt` to your
   computer.

3. **Add it to your project.** Rename it `custom_fruit.pt` and put it here:
   ```
   backend/app/ml/weights/custom_fruit.pt
   ```

4. **Install the extra dependency** (only needed for this path):
   ```
   pip install -r requirements-custom-model.txt
   ```

5. **Switch the backend to use it.** One environment variable:
   ```
   set USE_CUSTOM_MODEL=1          (Windows PowerShell: $env:USE_CUSTOM_MODEL=1)
   python -m uvicorn app.main:app --port 8000
   ```
   Without that variable set, the project uses the original pretrained
   model as before — nothing else changes.

## Checking it worked
Upload a photo with a clearly visible fruit from the 6 classes. The result
page should label it correctly. `training/train_custom_model.ipynb` step 5
also lets you test a photo right inside Colab before you even download
anything.

## Going further
- **More accuracy:** add more images to `dataset/train/images` +
  matching label `.txt` files in `dataset/train/labels`, then retrain.
- **More classes:** same idea — add labelled images for a new class,
  add its name to `dataset/data.yaml`, retrain.
- **Both general objects AND fruit:** keep `detector.py` (COCO) for
  everyday objects, and only call `detector_custom.py` (yours) when you
  specifically want fine-grained fruit type. This needs a small code
  change to `pipeline.py` — ask if you want this built.
