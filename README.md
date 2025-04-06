Hello! I'm so tired haha, but I'm going to try to get through this. This will walk you through setting up and understanding each piece, but sorry if it doesn't cover everything.

Just for clarity, in my eyes, this project has 3 major parts: The ML model we train, the OpenAI API interface for the user, the browser extension. The reason why the ML model is separated is because OpenAI limits how much you can interact with their model itself. In our initial conversation, we said we would code ChatGPT directly, or at least close to it, but it's not very reasonable it turns out. In addition to this, it's actually more realistic to train our own model because we can fine tune it better to our goal, as ChatGPT isn't specialized towards marking phishing emails. It _can_ do its best, but it may not be able to catch the more difficult examples of phishing.

## Setting up the python

First lets cover how to set up the ML model. Keep in mind, however, that we will need to add serialization later on once we get our model to the accuracy that we want it. We want to reduce false negatives as much as possible, and allow for false positives (we do not let phishing emails to be marked as safe, but marking safe emails as phishing are acceptable because it's a tradeoff between a security breach and mild user frustration).

1. Start python environment

Why do we use a virtual environment? This is standard practice because it lets us keep our python dependency versions consistent. It makes sure that dependency versions don't get messed up between different projects. Make sure to run your virtual environment whenever you want to install a dependency or run anything that involves python (i.e. scripts, FastAPI server, etc). Virtal environments are very large though, so we do not push those to the GitHub. It is placed in the .gitignore, so you need to make one yourself:
a. Create the python environment by first going to the /backend/ directory using `cd /backend` command. Then type `python -m venv venv` in terminal. This will automatically create the venv.
b. Technically you should be able to run with a line like `venv\Scripts\activate` but I've had problems with this in the past. This new line should make it work without issue: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and `.\venv\Scripts\Activate.ps1`.

2. Managing dependencies
   To get the most recent dependencies, you can run `pip install -r requirements.txt` to get all the python libraries used. It's always worth doing this before working to avoid accidentally redownloading something (especially if it ends up being another version!). If you want to write to this file, run the command `pip freeze > requirements.txt`. But I will say, be careful what you install because we don't want to clutter up our requirements too much unnecessarily.

3. Understanding the flow of data + Keys

I'm going to assume you guys have limited or no ML experience, so I want ot make sure everything is intuitive as possible. The main files we're going to be looking at in this stage are: load_monkeys.py/load_ling.py, preprocess.py, extraction.py, and training.py. Note: Do NOT run any scripts until this guide tells you to. There won't be any issues if you do, but it adds to the complexity of the setup.

a. load_monkeys.py and load_ling.py
Before we train our ML model, we need to install the datasets that we're going to train our model off of. For this project, we are using a technique called 'supervised learning'. This means the data we train on has 'labels' already included in the dataset. Our main purpose is to make a 'binary classification' model that will either mark a email as phishing (1) or non-phishing (0). 
EDIT: I changed the dataset we're using and took this Nazario dataset (essentially a gold standard research dataset) which I downloaded as such: http://monkey.org/~jose/phishing/phishing3.mbox
So this will give you an mbox file, which is basically a text file with thousands of (ideally) phishing emails. Please make a directory called 'data' in your backend folder, so `backend/data` and place that mbox file within the data. Now everything should work properly. Also, the Kaggle dataset was changed too. I now selected the Ling-Spam dataset, which labels things as either Spam (1) or Ham (0). More info is on the website below.
        
My code should ideally set everything up automatically, but you need to do some work as well. Go to the website `https://www.kaggle.com/datasets/mandygu/lingspam-dataset`. To install a dataset, you will need to make an account on Kaggle. Then, click your icon in the top right and click settings. There should be a section on the settings page called 'API' with a button called "Create New Token". If you click it, I believe it automatically starts the download for a 'kaggle.json'. This file stores your username and kaggle API key. Now go back to your IDE and create a new file in the backend directory called 'kaggle.env'. In this file, you will put your username and key in this format:

KAGGLE_USERNAME=KAGGLE_USERNAME_FROM_JSON_FILE
KAGGLE_KEY=KAGGLE_KEY_FROM_JSON_FILE

You do not need quotes around anything. Why are we doing this? We never want to push our API keys to a public GitHub Repo for security reasons. The dotenv Python library will help you get the username and key directly from other files. So basically this will load the datasets from Kaggle and save them somewhere on your computer.

b. preprocess.py
Before we can use a dataset, we need to ensure that the data within it is appropriate for our model to use. The Kaggle set provides 7 different datasets, so the code will merge these into one dataset for our model to use. The actual processing includes things thiss: if there are empty fields in the csv files, our model might use that data point incorrectly. The code then saves the "cleaned" dataset for later use.

c. extraction.py
Now we're moving closer to the ML process. The data that we're going to be analyzing are emails that include the subject, email body, and some other metadata for that specific email. Emails are basically just whole paragaphs, so how can we teach the computer to analyze an email? This is the process called 'feature extraction' or 'feature engineering'. We need to decide for ourselves what we want the ML model to look at (i.e. the number of URLs, the number of suspicious keywords/phrases, email length, number of uppercase letters, etc.). This is arguably going to be the most important part of this entire project for us since it directly influences the accuracy of our model. If our data features are weak, the model will be weak.

d. training.py
This is where the magic happens. This file alone is what calls all the previous functions and sets everything up for us. Before this point, you actually didn't have to do anything but make a Kaggle account. First, it will check if the dataset is loaded. If not, it'll call the dataset loader and return the absolute pathing to that directory. Then, if the preprocessed dataset, phishing_emails_cleaned.csv, is not found, it'll run that script and generate the file. Next, it will extract the features we discussed from the cleaned csv file and create one last mega-dataset with all of the previous data features (subject, body, label, etc.) with our custom data features.

Finally, the data will be run through an ML model. The primarily implements of ML are done through numpy, a library used for data manipulation and reading, and scikit-learn, which has hundreds of ML functions for us to use without directly implementing the mathematical formulas. In this current example, we have implemented a logistic regression model. For the sake of this document, I won't include a detailed explanation on what it is or how it works, but I'm very happy to get on call and discuss it at some point. The main separation here is between feature engineering and choosing a model. If we have well defined features, the model itself will come easily. Ideally we can test a few different ML models: Logistic Regression, Random Forests, Support Vector Machines. And then chose which would be most accurate and effective model. Again, this part is an oversimplification, but I'm happy to answer questions or get on call to chat about it as a group.

Finally finally, let's actually run some code. Make sure you're in the /backend directory and have the venv active. Then run `python training.py`. This will be doing a large number of things and will most likely **take a long time**. This will be the case any time we do feature engineering or train the model. Now, you may be asking how this will work in our application if it takes so long. We will be essentially "saving" our model using serialization techniques so the model is pretrained and ready to analyze individual examples later on. Anyways, after runnin the code, first an example of our features will show up (this shows what feature are currently being use). Then the datasets will be loaded and preprocessed + print a few examples of the new dataset. Next, we will extract features from the dataset and again print a few examples of the new dataset. Keep in mind, all of these steps won't be done every time, so it may be marginally faster later on (still a bit slow though; there's so much data!). Finally, the code shoul train the model and output the accuracy and other error measurements. When I run it, it shows about 70% accuracy. This is actually quite bad, so our purpose is to upgrade our model until it's very powerful in classification.

## Setting up FastAPI and OpenAI API

The FastAPI is going to be used as an interface between our AI model/OpenAI API and our browser extension. It does this by creating a REST framework that sends HTTP requests/responses between the two bodies. In your terminal, go to the /backend directory and make sure your virtual environment is on. Then, run the command `uvicorn main:app --reload`. FastAPI uses uvicorn to run its servers, and what this commmand is telling uvicorn to do is to run the 'app' that exists in 'main.py' (that's why it's main:app). If you want further understanding, you can go to `http://127.0.0.1:8000/docs` to see our endpoints and potentially even test them there, if they're simple enough.

Also in this file is the OpenAI API endpoints we'll be using, since we will acutally just feed the data from our model right into OpenAI, which will then generate a message. There is some 'prompt engineering' in this to generate more relevant text. This will be shown on our browser extension. In the next section, I'll show you how you can test an example for yourself.

## Setting up the browser extension.

Once you start the FastAPI server, there's actually not that many steps involved in testing this. In the 'extension' folder, we have the manifest.json (holds metadata), the popup.html for the visual elements, popup.js to connect our FastAPI endpoint with the extension, the css file, and a random icon. If you want to test this, here are your options:
a. On Chrome, go to `chrome://extensions/` and turn on 'Developer mode' in the top right. Then, click 'Load unpacked' and go to the extension directory on your file explorer. When you open the extension, will be added to your extensions. Open up the extension by clicking on it, and if your FastAPI server is on, you will see the endpoint text show up.
b. On Firefox, go to `about:debugging#/runtime/this-firefox` and click "Load Temporary Add-On". For this one, I just loaded the popup.html file. You can open up the extension and test it the same way as Chrome.

The good thing about this is your changes immediately are visible on the extension upon re-running it.

Alright well I hope this helps. This project is 80% design 20% work, so I think we got it :)
