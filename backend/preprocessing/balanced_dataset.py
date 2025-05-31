import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from sklearn.feature_extraction.text import TfidfVectorizer

# Adjustable parameters
input_csv_path = "../data/preprocessed/all_emails_cleaned.csv"
desired_phishing_ratio = 0.3  # Example: 30% phishing, 70% legit in training set
random_state = 42
test_size = 0.15
val_size = 0.15

print("🔄 Loading dataset...")
df = pd.read_csv(input_csv_path)
print(f"✅ Loaded {len(df)} rows.")

# Ensure no missing body or label
print("🧹 Dropping rows with missing Body or Label...")
df = df.dropna(subset=["Body", "Label"])
print(f"✅ Remaining rows: {len(df)}")

# 2. Split off test + validation sets first
print("✂️ Splitting into features and labels...")
X = df.drop("Label", axis=1)
y = df["Label"]

print("🔀 Splitting into train/test...")
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=test_size, stratify=y, random_state=random_state
)

print("🔀 Splitting train into train/val...")
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=val_size / (1 - test_size), stratify=y_temp, random_state=random_state
)

print(f"✅ Training samples: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")

# 3. Apply SMOTE to the training set
print("📝 Extracting text from training set...")
X_train_text = X_train["Body"]

print("🔠 Vectorizing text with TF-IDF...")
vectorizer = TfidfVectorizer(max_features=5000)
X_train_vec = vectorizer.fit_transform(X_train_text)
print(f"✅ TF-IDF shape: {X_train_vec.shape}")

# Apply SMOTE
print(f"🧪 Applying SMOTE with desired phishing ratio: {desired_phishing_ratio}...")
sm = SMOTE(sampling_strategy=desired_phishing_ratio, random_state=random_state)
X_train_resampled, y_train_resampled = sm.fit_resample(X_train_vec, y_train)
print(f"✅ After SMOTE: {X_train_resampled.shape[0]} samples")

# Reconstruct resampled DataFrame
print("📦 Reconstructing DataFrame from resampled data...")
X_train_resampled_df = pd.DataFrame(X_train_resampled.toarray(), columns=vectorizer.get_feature_names_out())
y_train_resampled_df = pd.DataFrame(y_train_resampled, columns=["Label"])

# Combine and save
print("💾 Saving validation and test sets...")
X_val["Label"] = y_val
X_test["Label"] = y_test
X_val.to_csv("../data/preprocessed/val.csv", index=False)
X_test.to_csv("../data/preprocessed/test.csv", index=False)

print("💾 Saving resampled training set...")
X_train_resampled_df["Label"] = y_train_resampled_df
X_train_resampled_df.to_csv("../data/preprocessed/train_resampled.csv", index=False)

print("✅ All datasets saved successfully!")
