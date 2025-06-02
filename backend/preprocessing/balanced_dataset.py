import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# --- Config ---
input_csv_path = "../data/preprocessed/all_emails_cleaned.csv"
phishing_ratios = [0.1, 0.3, 0.5]  # Percent of phishing for training
random_state = 42
test_size = 0.15
val_size = 0.15
realistic_test_ratio = 0.02  # Test set will be 2% phishing
output_dir = "../data/preprocessed/"

print("🔄 Loading dataset...")
df = pd.read_csv(input_csv_path)
df = df.dropna(subset=["Body", "Label"])
print(f"✅ Loaded and cleaned: {len(df)} rows.")

# --- Stratified split of full data ---
X = df.drop("Label", axis=1)
y = df["Label"]

# --- Create realistic test set with 2% phishing ---
print("🔀 Creating realistic test set (2% phishing)...")
phish_df = df[df["Label"] == 1]
legit_df = df[df["Label"] == 0]

test_phish = phish_df.sample(frac=realistic_test_ratio, random_state=random_state)
test_legit = legit_df.sample(n=len(test_phish) * 49, random_state=random_state)  # 1:49 phishing ratio
test_df = pd.concat([test_phish, test_legit]).sample(frac=1, random_state=random_state)

df_remaining = df.drop(test_df.index)

# Split remaining into training and validation
print("🔀 Splitting remaining into train/val sets...")
X_temp = df_remaining.drop("Label", axis=1)
y_temp = df_remaining["Label"]
X_train_full, X_val, y_train_full, y_val = train_test_split(
    X_temp, y_temp, test_size=val_size / (1 - test_size), stratify=y_temp, random_state=random_state
)

# Save raw test and validation sets (optional)
print("💾 Saving raw test and validation sets...")
test_df.to_csv(f"{output_dir}test.csv", index=False)
val_df = X_val.copy()
val_df["Label"] = y_val
val_df.to_csv(f"{output_dir}val.csv", index=False)

# --- Sentence Transformer model for embeddings ---
print("🧠 Loading sentence transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight, good balance of speed & quality

# --- Generate embeddings for validation and test sets ---
print("🔠 Generating embeddings for validation text...")
X_val_text = X_val["Body"].tolist()
X_val_embeds = model.encode(X_val_text, batch_size=64, show_progress_bar=True)

print("🔠 Generating embeddings for test text...")
X_test_text = test_df["Body"].tolist()
X_test_embeds = model.encode(X_test_text, batch_size=64, show_progress_bar=True)

# Save embeddings + labels for val and test
print("💾 Saving validation embeddings + labels...")
val_embedded_df = pd.DataFrame(X_val_embeds)
val_embedded_df["Label"] = y_val.values
val_embedded_df.to_csv(f"{output_dir}val_embed.csv", index=False)
print(f"✅ Saved validation embeddings: val_embed.csv ({len(val_embedded_df)} samples)")

print("💾 Saving test embeddings + labels...")
test_embedded_df = pd.DataFrame(X_test_embeds)
test_embedded_df["Label"] = test_df["Label"].values
test_embedded_df.to_csv(f"{output_dir}test_embed.csv", index=False)
print(f"✅ Saved test embeddings: test_embed.csv ({len(test_embedded_df)} samples)")

# --- Generate embeddings for training data ---
print("🔠 Generating embeddings for training text...")
X_train_text = X_train_full["Body"].tolist()
X_train_embeds = model.encode(X_train_text, batch_size=64, show_progress_bar=True)

# --- Loop through different ratios and SMOTE modes ---
for ratio in phishing_ratios:
    for use_smote in [False, True]:
        suffix = f"embed_smote_{int(ratio*100)}" if use_smote else f"embed_{int(ratio*100)}"

        output_file = f"{output_dir}train_{suffix}.csv"

        # ✅ Skip if file already exists
        if os.path.exists(output_file):
            print(f"⏭️ Skipping {output_file} (already exists)")
            continue  # Skip to the next loop

        print(f"\n⚙️ Generating dataset: train_{suffix}.csv")
        
        X_train_vec = X_train_embeds
        y_train = y_train_full.copy().values

        if use_smote:
            print(f"🧪 Applying SMOTE with phishing ratio {ratio}...")
            sm = SMOTE(sampling_strategy=ratio, random_state=random_state)
            X_resampled, y_resampled = sm.fit_resample(X_train_vec, y_train)
        else:
            print(f"✂️ Downsampling legitimate emails to phishing ratio {ratio}...")

            phish_mask = y_train == 1
            legit_mask = y_train == 0

            phish_indices = np.where(phish_mask)[0]
            legit_indices_pool = np.where(legit_mask)[0]

            desired_legit_count = int(len(phish_indices) / ratio - len(phish_indices))
            print(f"📐 Need {desired_legit_count} legit emails out of {len(legit_indices_pool)} available (sampling with replacement)")

            sampled_legit_indices = np.random.choice(legit_indices_pool, desired_legit_count, replace=True)

            selected_indices = np.concatenate([phish_indices, sampled_legit_indices])

            X_resampled = X_train_vec[selected_indices]
            y_resampled = y_train[selected_indices]

        # Save as CSV (embeddings + label)
        print("📦 Saving embeddings + labels...")
        df_resampled = pd.DataFrame(X_resampled)
        df_resampled["Label"] = y_resampled
        df_resampled.to_csv(f"{output_dir}train_{suffix}.csv", index=False)

        print(f"✅ Saved: train_{suffix}.csv ({len(df_resampled)} samples)")
        print("📊 Label counts:\n", pd.Series(y_resampled).value_counts())
