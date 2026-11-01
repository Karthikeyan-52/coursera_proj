# Library Management System CI/CD

A beginner-friendly Flask project that demonstrates Python linting and unit tests with GitHub Actions, followed by a Tekton/Buildah build and deployment to Red Hat OpenShift. The library uses in-memory data, so its contents reset when the application restarts.

## Features

- Welcome page at `/`
- List books with `GET /api/books`
- Add a book with `POST /api/books`
- Delete a book with `DELETE /api/books/<id>`
- JSON validation and useful HTTP status codes
- GitHub Actions workflow for flake8 and nose
- Six-step Tekton pipeline: cleanup, git-clone, flake8, nose, buildah, openshift-client
- OpenShift-compatible, non-root application container listening on port 8000

## Technologies

Python 3.11+, Flask, flake8, nose, Docker, Tekton, Buildah, and Red Hat OpenShift. CI and the container use Python 3.11.

## Run locally on Windows

Install Python 3.11 or newer, then open PowerShell in the `Library-CI-CD` folder. Create and activate a virtual environment, then install dependencies:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, allow it for the current terminal with:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Run linting, tests, and the application:

```powershell
flake8 app.py tests
$env:PYTHONPATH = (Get-Location).Path
python -m nose -v tests.test_app
python app.py
```

The application prints `SERVICERUNNING` on startup and is available at <http://localhost:8000>.
The `sitecustomize.py` compatibility shim lets nose 1.3.7 run on newer Python versions. The `PYTHONPATH` line ensures Python loads that shim before starting nose.

Example API requests in PowerShell:

```powershell
Invoke-RestMethod http://localhost:8000/api/books
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/books `
  -ContentType "application/json" -Body '{"title":"Dune","author":"Frank Herbert"}'
Invoke-RestMethod -Method Delete http://localhost:8000/api/books/1
```

## GitHub Actions

The repository-root workflow is `../.github/workflows/workflow.yml`. GitHub only discovers Actions workflows under the repository root `.github/workflows/`; this repository stores the project itself in the `Library-CI-CD/` subfolder. Push changes to `main` (or open a pull request targeting `main`) and make sure Actions are enabled under **Settings → Actions → General**. It installs this folder's `requirements.txt`, runs flake8, and then runs nose. No repository secrets are needed for these checks.

## Build and run the container locally

From the project directory:

```powershell
docker build -t library-cicd:local .
docker run --rm -p 8000:8000 library-cicd:local
```

The container runs as UID 1001 (and is prepared for OpenShift's arbitrary non-root UID), listens on `0.0.0.0:8000`, and prints `SERVICERUNNING` in its container logs. Check with `docker logs <container-id>`.

## Deploy to OpenShift with Tekton

These commands assume `oc` is installed, you are logged into an OpenShift cluster, and the OpenShift Pipelines Operator is installed. Replace `YOUR_NAMESPACE` with the actual OpenShift project name in `.tekton/pipelinerun.yml` and `PROJECT_NAMESPACE` in `openshift/deployment.yml`. The image reference in the PipelineRun must use the same namespace as the OpenShift project.

### 1. Select the project and create the workspace PVC

```powershell
oc project YOUR_NAMESPACE
oc apply -f .tekton/pvc.yml
```

The PVC is named `library-cicd-workspace`, uses `ReadWriteOnce`, and requests 1 GiB. If your cluster has no default StorageClass, edit its `storageClassName` before applying.

### 2. Create the application resources

Replace `PROJECT_NAMESPACE` in `openshift/deployment.yml` with the namespace name, then apply the resources:

```powershell
oc apply -f openshift/deployment.yml
oc apply -f openshift/service.yml
oc apply -f openshift/route.yml
```

The Deployment image placeholder is:

```text
image-registry.openshift-image-registry.svc:5000/PROJECT_NAMESPACE/library-cicd:latest
```

The PipelineRun supplies this same image to Buildah and the deployment task.

### 3. Install Tekton tasks and pipeline

```powershell
oc apply -f .tekton/tasks.yml
oc apply -f .tekton/pipeline.yml
oc create serviceaccount pipeline
oc adm policy add-role-to-user edit -z pipeline -n YOUR_NAMESPACE
oc adm policy add-role-to-user system:image-builder -z pipeline -n YOUR_NAMESPACE
```

The Buildah task uses privileged mode for compatibility with the standard Buildah storage/build workflow. A cluster administrator must grant the `privileged` SCC to this pipeline service account if the cluster's policy requires it:

```powershell
oc adm policy add-scc-to-user privileged -z pipeline -n YOUR_NAMESPACE
```

This permission is for the image-build task only; the deployed Flask container itself runs non-root. Follow your organization's cluster policy before granting elevated permissions.

### 4. Set the Git URL and image, then run

Edit `.tekton/pipelinerun.yml` and replace both occurrences of `YOUR_NAMESPACE`. Its Git URL already points to this repository. The image value should be:

```text
image-registry.openshift-image-registry.svc:5000/YOUR_NAMESPACE/library-cicd:latest
```

Import and start the run:

```powershell
oc create -f .tekton/pipelinerun.yml
oc get pipelineruns
oc get taskruns
```

Watch task status and logs:

```powershell
tkn pipelinerun logs -f -L
```

Alternatively, find the relevant TaskRun and inspect its logs:

```powershell
oc get pods
oc logs <task-pod-name> -c step-nose
```

### 5. Verify the deployment and collect application logs

```powershell
oc rollout status deployment/library-cicd
oc get deployment,service,route
oc get pods -l app=library-cicd
oc logs deployment/library-cicd
```

The application log should contain the exact startup line `SERVICERUNNING`. Open the URL shown by `oc get route library-cicd` to visit the home page.

## Push the project to GitHub

Run these commands from the repository root (the parent folder of `Library-CI-CD`) after setting its `origin` remote to your GitHub repository:

```powershell
git add Library-CI-CD .github
git commit -m "Create Library Management System CI/CD project"
git push origin main
```

If Git prompts for credentials, authenticate with GitHub's supported browser flow or a credential manager; do not put a personal access token in the remote URL.
