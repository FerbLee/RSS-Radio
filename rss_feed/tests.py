from django.test import TestCase
from .models import Image,UserProfile, Program, Tag
from .models import DEFAULT_IMAGE_PATH,DEFAULT_AVATAR_PATH, ADMT_OWNER, ADMT_ADMIN
from django.contrib.auth.models import User

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
        
        # Efective deletion of file is tested manually
        
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


class UserProfileModelTests(TestCase): 
    
    
    def test_update_user_profile_creation(self):
        
        user = User.objects.create(username='test_user')
        self.assertIsInstance(user.userprofile, UserProfile)
        
    
    def test_delete(self):
        
        user = User.objects.create(username='test_user2')
        userp = user.userprofile
        
        image = Image.objects.create(name='avatar1',path='path/to/avatar')
        image_id = image.id
        
        userp.avatar = image
        userp.save()
        userp_id = userp.id
        
        userp.delete()
        
        userp2 = list(UserProfile.objects.filter(pk=userp_id))
        self.assertEqual(userp2,[])
        
        image2 = list(Image.objects.filter(pk=image_id))
        self.assertEqual(image2,[])
        
        
    def test_update_user_profile_deletion(self):
        
        user = User.objects.create(username='test_user3')
        self.assertIsInstance(user.userprofile, UserProfile)
    
        up_id = user.userprofile.id
        
        user.delete()
        up = list(UserProfile.objects.filter(pk=up_id))
        self.assertEqual(up,[])


class TagModelTests(TestCase):
    
    
    def test_decrease_times_used(self):
        
        t = Tag.objects.create(name='T1',times_used=5)
        t.decrease_times_used()
        
        t1 = Tag.objects.get(name='T1')
        self.assertEqual(t1.times_used,4)
        
        t1.decrease_times_used(quantity=7)
        
        t2 = Tag.objects.get(name='T1')
        self.assertEqual(t2.times_used,0)


    def test_clean_name(self):
        
        name = "   CaTEgory "
        expected = "category"
        
        self.assertEqual(Tag.clean_name(name),expected)
        
        

class ProgramModelTests(TestCase): 
    
        
    def setUp(self):
        
        rssl = 'http://dummy_linl.xml'
        p_image = Image.objects.create(name='p_image1',path='path/to/p_image1')
        
        p1 = Program.objects.create(name='TestProgram1',rss_link=rssl,image=p_image)
        
        u1 = User.objects.create(username='userp1')
        u2 = User.objects.create(username='userp2')
        User.objects.create(username='userp3')
        
        p1.programadmin_set.create(user=u1,type=ADMT_OWNER[0])
        p1.programadmin_set.create(user=u2,type=ADMT_ADMIN[0])
        
        t1 = Tag.objects.create(name='pt1',times_used=1)
        t2 = Tag.objects.create(name='pt2',times_used=2)
        
        p1.tag_set.add(t1)
        p1.tag_set.add(t2)
        
    
    def test_check_user_is_admin(self):
        
        p1 = Program.objects.get(name='TestProgram1')
        u1 = User.objects.get(username='userp1')
        u2 = User.objects.get(username='userp2')
        u3 = User.objects.get(username='userp3')
        
        self.assertTrue(p1.check_user_is_admin(u1,ADMT_OWNER[0]))
        self.assertFalse(p1.check_user_is_admin(u1,ADMT_ADMIN[0]))
        self.assertTrue(p1.check_user_is_admin(u2,ADMT_ADMIN[0]))
        self.assertFalse(p1.check_user_is_admin(u2,ADMT_OWNER[0]))
        self.assertFalse(p1.check_user_is_admin(u3))
        
    
    def test_delete(self):
        
        p1 = Program.objects.get(name='TestProgram1')
        p1_id = p1.id
        img_id = p1.image.id
        
        p1.delete()
        
        p2 = list(Program.objects.filter(pk=p1_id))
        self.assertEqual(p2,[])
        
        img2 = list(Image.objects.filter(pk=img_id))
        self.assertEqual(img2,[])
        
        t1 = Tag.objects.get(name='pt1')
        t2 = Tag.objects.get(name='pt2')
        
        self.assertEqual(t1.times_used,0)
        self.assertEqual(t2.times_used,1)
        
    