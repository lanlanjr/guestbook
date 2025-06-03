# Deploying to Vercel

This guide will help you deploy your Guestbook application to Vercel.

## Prerequisites

1. A [Vercel account](https://vercel.com/signup)
2. [Vercel CLI](https://vercel.com/docs/cli) installed (optional for local testing)

## Deployment Steps

### 1. Set up Environment Variables

In the Vercel dashboard, you'll need to set up the following environment variables:

- `SECRET_KEY`: A secure random string for Flask's session encryption
- `DATABASE_URL`: (Optional) If you want to use a database other than SQLite

For SQLite, you'll need to use Vercel's persistent storage since Vercel functions are stateless. Consider using a database service like Vercel Postgres or an external database.

### 2. Deploy using Git Integration

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)
2. Import your project in the Vercel dashboard
3. Configure your project settings
4. Deploy

### 3. Deploy using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from your project directory
vercel
```

## Important Notes

1. **Database**: The SQLite database in the instance folder will not persist between deployments or function invocations on Vercel. Consider using:
   - Vercel Postgres
   - Another database service (MongoDB Atlas, Supabase, etc.)

2. **File Storage**: Uploaded files in the static/uploads directory will not persist between deployments. Consider using:
   - AWS S3
   - Cloudinary
   - Vercel Blob Storage

3. **Environment Variables**: Make sure to set up your SECRET_KEY in the Vercel dashboard.

## Modifying the App for Production

For a production deployment, you should modify the app to:

1. Use an external database instead of SQLite
2. Use cloud storage for file uploads
3. Ensure all secrets are stored as environment variables

## Troubleshooting

If you encounter issues with your deployment:

1. Check the Vercel deployment logs
2. Ensure all dependencies are correctly specified in requirements.txt
3. Verify that your environment variables are correctly set
4. Check that your vercel.json configuration is correct 