Project Setup and Installation Guide

Prerequisites

Ensure you have the following installed on your system:

Python 3.10 or later

Git

Pip (Python package manager) 

Installation Instructions

Follow these steps to set up the project and resolve package issues:

1. Clone the Repository

2. Set Up Git User Identity

If you haven't set up your Git identity yet, run:

3. Install Required Python Packages

Upgrade and reinstall numpy to fix import issues:

4. Running the Script

To extract keywords,summary of the pdf run:

5. Pushing Changes to GitHub

If you want to push your changes:

6. Using a GitHub Personal Access Token

Since GitHub removed password authentication, use a personal access token for authentication:

Then push the changes again:

Troubleshooting

If you encounter a numpy.core.multiarray failed to import error, reinstall numpy using:

If transformers is outdated, upgrade it:

