import cloudinary.uploader
import cloudinary

# Utility function to upload files to Cloudinary
def upload_to_cloudinary(file, folder_name="fintechapp_user_uploads"):
    """
    Uploads an image to Cloudinary in the specified folder and returns the URL.
    The folder will be created automatically by Cloudinary if it doesn't exist.
    """
    result = cloudinary.uploader.upload(
        file,
        folder=folder_name,
        resource_type="auto",
        use_filename=True,
        unique_filename=True,
        overwrite=False
    )
    return result["secure_url"]
