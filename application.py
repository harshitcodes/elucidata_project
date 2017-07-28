import os
import os
from flask import Flask, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask import send_from_directory
import pandas as pd

UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS = set(['csv', 'xlsx'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    <a href = "/create_childsets"><button> Create Child Dataset</button> </a><br>
    <a href = "/retention_time_roundoff"><button> Round off retention time </button> </a><br>
    <a href = "/mean"><button> Calculate Mean Across Sample </button> </a><br>
    '''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/create_childsets')
def create_child_sets():
    """
    creates 3 child datasets for
    the main dataframe based on
    keystrings in the dataframe col
    """
    df = pd.read_excel("./uploads/eluci_data.xlsx")
    children = [' PC', ' LPC', ' plasmalogen']
    for i in children:
        a = df[df['Accepted Compound ID'].str.contains(i, na = False)]
        a.to_excel('./datasets/{}.xlsx'.format(i))

    return redirect(url_for('upload_file'))


@app.route('/retention_time_roundoff')
def retention_time_roundoff():
    """
    rounds off the retention time for each sample
    and adds the col to the main df.
    """
    df = pd.read_excel("./uploads/eluci_data.xlsx")
    df['Rounded Retention Time'] = df['Retention time (min)'].round()
    writer = pd.ExcelWriter('./datasets/rounded_retention_time.xlsx')
    df.to_excel(writer)
    writer.save()
    flash("Look in the datasets folder")
    return redirect(url_for('upload_file'))


@app.route('/mean')
def mean_across_samples():
    df = pd.read_excel("./datasets/rounded_retention_time.xlsx")
    new_df = pd.DataFrame()
    a = df.ix[:,3:1049]
    new_df = a
    new_df.insert(0, 'retention time roundoff', df['Rounded Retention Time'])
    new_df.insert(1, 'mean', df.ix[:,3:1049].mean(axis=1))
    new_df.to_excel('./datasets/mean_sample.xlsx')
    return redirect(url_for('upload_file'))




if __name__ == '__main__':
    app.secret_key = "thisismysupersecret"
    app.debug = True
    app.run(host='127.0.0.1', port=8000)
