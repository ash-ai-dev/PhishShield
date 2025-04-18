Alright this document will serve as a current "state of the project". At the top, I will also list the current features that need to be implemented or improved.

## Current Tasks
- The extension needs to be visually updated significantly
- We need to update the Gmail fetching such that it will get more emails than just the last one. This in itself is not complicated, but requires specific design to handle what the program will do if many phishing emails are detected (flag those sender addresses?, save the examples somewhere?, give a button to send all to the trash?)
- There should be some interface to handle when the PhishShield marks something as phishing, but the user does trust that sender. We should carefully mark this sender as potentially unsafe regardless
- The application should work in real time if the Gmail page is available
- The OpenAI API prompt is currently very simple. Maybe research prompt engineering and see how you can improve on it. We previously dicussed making a "user education" portion, but lets table that for now
- The ML model is surprisingly effective, but can be improved at every step. The data can be more expansive + cleaner, the features extracted could be more effective. The models themselves are fine, but we should explore others
- If you want to be even cooler later on, work on trying to implement deep learning through Neural Network models, but this is to be done AFTER everything else above

# Pipeline
As I said previously, this project is broken up into 3 separate sections: The ML model we're using, the OpenAI, and the browser extension.

The current pipeline flow is: 
- User clicks the button on the extension
- The extension uses JS to fetch data from the user's Gmail using the Gmail API
- The Gmail data that was fetched will send the data to our FastAPI endpoint /email
- Then, within this endpoint, the /explain endpoint is called. The email data is sent to this endpoint, where our ML model is run.
- The ML Model will give a prediction, and if the reulting classification is phishing, it'll aask the OpenAI API to generate some content about why this email was classified as phishing.
- This content is then POSTed back to the JS file and send the generated explanation back to the extension

## Browser Extension
The browser extension is implemented using a combination of a manifest.json (using manifest3) file, a simple HTML page (popup.html), and a JavaScript script (popup.js) that interacts with the Gmail interface. 
What the manifest.json does is it configures the extension’s permissions, specifying access to the Gmail tab. This is the most important file here, as the manifest.json file requests permissions like accessing user identity and storing data, and specifies the websites it can communicate with (OpenAI and Google APIs).
The file also points to the extension script (popup.js), defines the popup UI (popup.html) and icon (icon.png), configures OAuth 2.0 for secure Gmail access with read-only permission, and allows connections from Google websites.
When the extension is activated, it opens a popup interface defined by the HTML file, which includes a button labeled to fetch the most recent email. 
After clicking the button, the popup.js JavaScript script runs in the context of the Gmail inbox, scanning the currently visible email thread and extracting the body content of the most recent email using DOM manipulation. 
This content is then sent to the  backend server for phishing detection.

## Gmail API
I don't want to get into this too much right now because I did it so fast, but essentially what I had to do was create a project on Google Cloud Projects and enable the Gmail API. 
Then, I created OAuth2.0 client for the chrome extension. This essentially is the setup for making real extensions. In fact, we could actually upload this to the real Chrome web store when we're done. 
There's not a lot of development here, but this is necessary for the extension to be usable.

## ML Model

load_ling.py/load_monkeys.py             
The process begins by gathering two key datasets: the Nazario Phishing Corpus and the Ling-Spam Dataset. 
The Nazario dataset is used to train the model on phishing emails, while the Ling-Spam Dataset provides labeled legitimate emails to create a balanced dataset. 
This balance is required because the model needs to learn how to classify (find the difference and choose a label for any given email), and the best way to do that is to show it examples of safe emails as well as harmful emails.            

preprocess.py               
The email body text from both datasets is extracted, and preprocessing steps such as removing headers, HTML tags, special characters, and duplicate messages are applied. Preprocessing is important because that unnecessary information, as well as empty data fields, can make our model confused.
          
extraction.py             
After preprocessing (cleaned), the next step is to extract some additional features from it. This is called feature engineering, and it's the action of producing additional data, or changing the data to better match our goal. 
       
training.py               
Then the dataset is split into training and testing sets in an 80/20 ratio. This is a standard method because it allows us to train our model on the data, but also have another set of data to test or prove that the model is effective (testing on the same data is unsafe, as our model would already know the answers!)
The labels are: phishing emails marked as class 1 and legitimate emails as class 0.
Several machine learning models are tested to determine the best fit for phishing detection: Logistic Regression, Random Forests, and Naive Bayes. The Random Forest Classifier so far is outputting the highest performance. 
The trained model is evaluated on metrics like accuracy, precision, recall, and F1 score, which gauge its effectiveness in identifying phishing emails. 
The model is then serialized for deployment using joblib (kind of like saving the model for later use as files rather than having to run the training.py again).

## OpenAI API
At the current stage of the project, the OpenAI API is used for creating AI-generated feedback to users when a phishing email is detected. 
Prompt engineering is important here as we need to make sure that the responses are both informative and user-friendly. 
The prompt currently in use tells the model to behave as a cybersecurity expert. 
It is very simple but relatively effective because of how extensive GPT's model is and asks the model to explain why the detected email may be considered phishing based on its content.  
