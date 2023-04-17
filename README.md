# 🐍 Yatube: Emulating a Social Network 📱🌐

![push workflow](https://github.com/AleksandraMikh/yatube_final/actions/workflows/python-app.yml/badge.svg)

Yatube is a web application that helps you connect and share content with your friends and family. It emulates a social network and has a variety of features that will help you stay connected with people you care about.

Some of the features included in Yatube are:

- Editable posts with pictures, so you can share meaningful stories and moments with your followers.
- A feed that allows you to see the latest posts from the people you follow, so you never miss important updates.
- Follow and unfollow, giving you complete control over who you connect with and what content you see.
- Authorization, so you can keep your account and data safe at all times.
- Editable comments, allowing you to engage in thoughtful discussions and give feedback.

With Yatube, you'll be able to keep in touch with the people that matter most to you, all while sharing your own unique perspective on life. Try it out today and see how it can transform the way you connect online!

## 🚀 Installation and Launch

To install and launch this application, please follow the instructions below:

1. Clone the repository and navigate to the project directory:

```
git clone https://github.com/AleksandraMikh/yatube_final.git
cd yatube_final
```

2. Create and start virtial environment and install the required packages using pip:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

If you got problems with Pillow set the version 8.3.1 in requirements.txt

```
Pillow == 8.3.1
```

And then run again 

```
pip install -r requirements.txt
```

3. Navigate to project directory, create the database and run database migrations:

```
cd yatube
python manage.py migrate
```

4. Create a superuser:

```
python manage.py createsuperuser
```

5. Run the development server:

```
python manage.py runserver
```

6. Visit `http://localhost:8000` in your web browser to see the app in action.

## 🌟 Application functionality

### Create superuser

Create superuser to get access to adminpanel and manage users and posts. To create superuser execute a command:

        python manage.py createsuperuser

and follow instructions on the monitor 🖥.

### Adminpanel

Adminpanel can be accessed on the endpoint http://localhost:8000/admin/. 
If you forgot login or password simply create new superuser.

On this page admin can create, update or delete users, posts and goups for posts. Posts can be created or deleted via regular user also. Groups can be managed only via adminpanel.

### Creating and editing posts and comments

To create new posts and comments, the user must register in the system and then log in to the website. After that, they can create new posts, add photos, and edit their own posts and comments.

That's it! If you have any questions, please feel free to contact me https://t.me/mikhaidoku.
