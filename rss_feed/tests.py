from django.test import TestCase
from .models import Image
from .models import DEFAULT_IMAGE_PATH,DEFAULT_AVATAR_PATH

# Create your tests here.


class ImageModelTests(TestCase):
    
    
    def test_default_program_image_creation(self):
        
        def_image = Image.default_program_image_creation()
        
        alt_text_def = 'default-image'
        
        #Check correct atb
        self.assertEqual(def_image.name, 'Program-Episode default image')
        self.assertEqual(def_image.alt_text,alt_text_def)
        self.assertEqual(def_image.path, DEFAULT_IMAGE_PATH)
        
        #Check in database
        dbi = list(Image.objects.filter(alt_text=alt_text_def))
        self.assertNotEqual(dbi, [])
        self.assertEqual(dbi[0].pk,def_image.pk)
    
    
    def test_get_default_program_image(self):
        
        image = Image.get_default_program_image()
        self.assertEqual(image.path,DEFAULT_IMAGE_PATH)
        
    
    def test_default_avatar_creation(self):
        
        def_image = Image.default_avatar_creation()
        
        alt_text_def = 'default-avatar'
        
        #Check correct atb
        self.assertEqual(def_image.name, 'User Avatar default image')
        self.assertEqual(def_image.alt_text,alt_text_def)
        self.assertEqual(def_image.path,DEFAULT_AVATAR_PATH)
        
        #Check in database
        dbi = list(Image.objects.filter(alt_text=alt_text_def))
        self.assertNotEqual(dbi, [])
        self.assertEqual(dbi[0].pk,def_image.pk)
    
    
    def test_get_default_avatar(self):
        
        image = Image.get_default_avatar()
        self.assertEqual(image.path,DEFAULT_AVATAR_PATH)
    
    
    def test_delete(self):
        
        #Try to delete default image
        def_image = Image.get_default_avatar()
        def_image.delete()
        def_image2 = Image.get_default_avatar()
        self.assertEqual(def_image2,def_image)
        
        #Try to delete regular image
        img = Image()
        img.name='test_image'
        img.path='path/to/file'
        img.save()
        img_pk = img.pk
        img.delete()
        
        img2 = list(Image.objects.filter(pk=img_pk))
        self.assertEqual(img2,[])
        
    
    
    