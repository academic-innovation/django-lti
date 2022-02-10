# Contributing to django-lti

Contributions are encouraged. Checkout the [help wanted][1] tag for
issues to work on. Follow the steps below to get started.

## Step 0: Setup your SSH key

Start by [adding your SSH key to GitLab][2].

## Step 1: Clone the repo

```
git clone git@gitlab.umich.edu:academic-innovation/lti/django-lti.git
```

## Step 2: Install development dependencies

Make sure you're working in a virtual env and install
development dependencies with `pip install -r requirements.txt`.

## Step 3: Checkout a new branch

Check out a new branch for your work.

```
git checkout -b my-awsome-feature main
```

## Step 4: Run quality checks

Before submitting a merge request, run quality checks locally
with `nox`.

## Step 5: Push your branch and create a merge request

```
git push origin my-awesome-feature
```

[1]: https://gitlab.umich.edu/academic-innovation/lti/django-lti/-/issues?label_name%5B%5D=help+wanted
[2]: https://gitlab.umich.edu/-/profile/keys