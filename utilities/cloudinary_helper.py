import cloudinary.uploader
import cloudinary

def upload_image_to_cloudinary(image_file, folder_name="fintechapp_user_images"):
    """
    Uploads an image to Cloudinary in the specified folder and returns the URL.
    The folder will be created automatically by Cloudinary if it doesn't exist.
    """
    result = cloudinary.uploader.upload(
        image_file,
        folder=folder_name,
        use_filename=True,
        unique_filename=True,
        overwrite=False
    )
    return result["secure_url"]
