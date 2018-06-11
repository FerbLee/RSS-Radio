from django.test import TestCase
from django.contrib.auth.models import User
import os,feedparser,datetime
import pytz

from .models import Image,UserProfile, Program, Tag, Episode, Comment, Vote, Station
from .models import DEFAULT_IMAGE_PATH,DEFAULT_AVATAR_PATH,ADMT_OWNER,ADMT_ADMIN,LIKE_VOTE,DISLIKE_VOTE,CO_DISABLE
from .models import IVOOX_TYPE, RADIOCO_TYPE, PODOMATIC_TYPE

from .rss_link_parsers import find_image_in_html,create_image,get_tag_instance
from .rss_link_parsers import ParserRadioco, ParserIvoox, ParserPodomatic

from .update_rss_daemon import ud_iterate_program_table


# Create your tests here.

TEST_AUX_FILE_PATH='/home/fer/eclipse-workspace/RSS-Radio/test_aux_files/'


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
        
        rssl = 'http://dummy_link.xml'
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
        
        
        
class EpisodeModelTests(TestCase): 
    
        
    def setUp(self): 
        
        rssl = 'http://dummy_link2.xml'
        p1 = Program.objects.create(name='TestProgram2',rss_link=rssl)
        
        u1 = User.objects.create(username='usere1')
        u2 = User.objects.create(username='usere2')
        u3 = User.objects.create(username='usere3')
        
        p1.programadmin_set.create(user=u1,type=ADMT_OWNER[0])
        p1.programadmin_set.create(user=u2,type=ADMT_ADMIN[0])
        
        e_image = Image.objects.create(name='e_image1',path='path/to/e_image1')
        audio_file = 'http://episode.audio/file.ogg'
        e1 = Episode.objects.create(program=p1,title='TestEpisode1',file=audio_file,image=e_image)
        
        t1 = Tag.objects.create(name='et1',times_used=1)
        t2 = Tag.objects.create(name='et2',times_used=2)
        
        e1.tag_set.add(t1)
        e1.tag_set.add(t2)
        
        e1.vote_set.add(Vote.objects.create(episode=e1,user=u1,type=LIKE_VOTE[0])) 
        e1.vote_set.add(Vote.objects.create(episode=e1,user=u2,type=LIKE_VOTE[0]))
        e1.vote_set.add(Vote.objects.create(episode=e1,user=u3,type=DISLIKE_VOTE[0])) 
        
        p2 = Program.objects.create(name='TestProgram3',rss_link=rssl,comment_options=CO_DISABLE[0])
        Episode.objects.create(program=p2,title='TestEpisode2',file=audio_file,image=e_image)
        
    
    def test_get_upvote_number(self):
        
        e1 = Episode.objects.get(title='TestEpisode1')
        
        self.assertEqual(e1.get_upvote_number(),2)
        
    
    def test_get_downvote_number(self):
        
        e1 = Episode.objects.get(title='TestEpisode1')
        
        self.assertEqual(e1.get_downvote_number(),1)
        
    
    def test_check_user_is_admin(self):
        
        e1 = Episode.objects.get(title='TestEpisode1')
        u1 = User.objects.get(username='usere1')
        u2 = User.objects.get(username='usere2')
        u3 = User.objects.get(username='usere3')
        
        self.assertTrue(e1.check_user_is_admin(u1,ADMT_OWNER[0]))
        self.assertFalse(e1.check_user_is_admin(u1,ADMT_ADMIN[0]))
        self.assertTrue(e1.check_user_is_admin(u2,ADMT_ADMIN[0]))
        self.assertFalse(e1.check_user_is_admin(u2,ADMT_OWNER[0]))
        self.assertFalse(e1.check_user_is_admin(u3))     
        
    
    def test_check_comments_enabled(self):    
    
        e1 = Episode.objects.get(title='TestEpisode1')
        self.assertTrue(e1.check_comments_enabled())
        
        e2 = Episode.objects.get(title='TestEpisode2')
        self.assertFalse(e2.check_comments_enabled())
        
    
    def test_delete(self):
        
        e1 = Episode.objects.get(title='TestEpisode1')
        e1_id = e1.id
        
        e1.delete()
        
        e2 = list(Episode.objects.filter(pk=e1_id))
        self.assertEqual(e2,[])
        
        t1 = Tag.objects.get(name='et1')
        t2 = Tag.objects.get(name='et2')
        
        self.assertEqual(t1.times_used,0)
        self.assertEqual(t2.times_used,1)
        

class StationModelTests(TestCase): 
    
        
    def setUp(self): 
        
        logo = Image.objects.create(name='logo1',path='path/to/logo1')
        p_img = Image.objects.create(name='p_image1',path='path/to/p_image1')
        
        s1 = Station.objects.create(name='RadioTest1',profile_img=p_img,logo=logo) 

        u1 = User.objects.create(username='users1')
        u2 = User.objects.create(username='users2')
        User.objects.create(username='users3')
        
        s1.stationadmin_set.create(user=u1,type=ADMT_OWNER[0])
        s1.stationadmin_set.create(user=u2,type=ADMT_ADMIN[0])
    
    
    def test_check_user_is_admin(self):
        
        s1 = Station.objects.get(name='RadioTest1')
        u1 = User.objects.get(username='users1')
        u2 = User.objects.get(username='users2')
        u3 = User.objects.get(username='users3')
        
        self.assertTrue(s1.check_user_is_admin(u1,ADMT_OWNER[0]))
        self.assertFalse(s1.check_user_is_admin(u1,ADMT_ADMIN[0]))
        self.assertTrue(s1.check_user_is_admin(u2,ADMT_ADMIN[0]))
        self.assertFalse(s1.check_user_is_admin(u2,ADMT_OWNER[0]))
        self.assertFalse(s1.check_user_is_admin(u3))  
        
    
    def test_delete(self):
        
        s1 = Station.objects.get(name='RadioTest1')
        s1_id = s1.id
        logo_id = s1.logo.id
        p_img_id = s1.profile_img.id
        
        s1.delete()
        
        s2 = list(Station.objects.filter(pk=s1_id))
        self.assertEqual(s2,[])
        
        logo2 = list(Image.objects.filter(pk=logo_id))
        self.assertEqual(logo2,[])
        
        p_img2 = list(Image.objects.filter(pk=p_img_id))
        self.assertEqual(p_img2,[])



class AuxFuncitonsRSSLPTests(TestCase):
    

    def test_find_image_in_HTML(self):
        
        html_file = TEST_AUX_FILE_PATH + 'description.html'
        expected_link = 'https://i1.wp.com/spoiler.cuacfm.org/wp-content/uploads/sites/2/2018/04/1453377486-sopranos.jpg'
        
        with open(html_file, 'r') as myfile:
            
            html_text=myfile.read().replace('\n', '')
        
        self.assertEqual(find_image_in_html(html_text)[0],expected_link)
        
    
    def test_create_image(self):
        
        image_url = 'https://i1.wp.com/spoiler.cuacfm.org/wp-content/uploads/sites/2/2018/04/1453377486-sopranos.jpg'
        expected_name_subchain = '1453377486-sopranos.jpg'
        
        i1 = create_image(image_url)

        self.assertIsInstance(i1, Image)
        self.assertEqual(i1.name,expected_name_subchain)
        self.assertTrue(os.path.isfile(i1.path.path))
        
        try:
            # Cleans the local file createad
            i1.delete()
        except:
            pass
    
    
    def test_get_tag_instance(self):
    
        tag1 = "rlpTAG1  "
        tag2 = " Rlptag1"
        
        t1 = get_tag_instance(tag1)
        t2 = get_tag_instance(tag2)
        
        self.assertEqual(t1.id, t2.id)
        self.assertEqual(t1.times_used, 1)
        self.assertEqual(t2.times_used,2)
        
    

class ParserIvooxRSSLPTests(TestCase):


    def initialize_test(self):
        
        RSS_file = TEST_AUX_FILE_PATH + 'hasta-los-kinders_original.xml'
        feed_dict = feedparser.parse(RSS_file)
        u1 = User.objects.create(username='userRSSLP1')
        
        return ParserIvoox(RSS_file,u1),feed_dict


    def test_get_entry_list(self):
        
        rlp,fd = self.initialize_test()
        el = rlp.get_entry_list(fd)

        self.assertIsInstance(el,list)
        self.assertIsInstance(el[0],dict)
        

    def test_parse_program(self):

        program_web = 'http://www.ivoox.com/podcast-hasta-los-kinders_sq_f14062_1.html'
        rlp,fd = self.initialize_test()
        
        p1 = rlp.parse_program(fd)
        
        self.assertEqual(p1.name,'Hasta Los Kinders')
        self.assertEqual(p1.language,'es-ES')
        self.assertEqual(p1.original_site,program_web)
        self.assertEqual(p1.rss_link_type,IVOOX_TYPE[0])
        
    
    def test_parse_episode(self):
       
        rlp,fd = self.initialize_test()
        
        #Expected info
        exp_titlte = 'CiudadanoKinders: Cómo hacer un monólogo'
        exp_pub_date = datetime.datetime(2010, 9, 17, 20, 45, 24, tzinfo=pytz.utc)
        exp_file = 'http://www.ivoox.com/ciudadanokinders-como-hacer-monologo_mf_368919_feed_1.mp3'
        exp_web = 'http://www.ivoox.com/ciudadanokinders-como-hacer-monologo-audios-mp3_rf_368919_1.html'
        exp_original_id = 'http://www.ivoox.com/368919'
        
        p1 = rlp.parse_program(fd)
        entry_dict = rlp.get_entry_list(fd)[0]
        
        e1 = rlp.parse_episode(entry_dict,p1)
        
        self.assertIsInstance(e1,Episode)
        self.assertEquals(e1.title,exp_titlte)
        self.assertEquals(e1.publication_date,exp_pub_date)
        self.assertEquals(e1.file,exp_file)
        self.assertEquals(e1.original_site,exp_web)
        self.assertEquals(e1.original_id,exp_original_id)
    
    
    # From superclass
    def test_parse_and_save(self):
    
        rlp,_ = self.initialize_test()
        
        p1 = rlp.parse_and_save()
        self.assertIsInstance(p1,Program)
        
        p1_id = p1.id
        p2 = list(Program.objects.filter(pk=p1_id))
        self.assertNotEqual(p2,[])
        
        p2 = p2[0]
        
        self.assertEqual(p2.tag_set.count(),1)
        self.assertEqual(p2.tag_set.all()[0].name,'comedy')
        self.assertIsInstance(p2.image,Image)
        
        
        self.assertEqual(p2.episode_set.count(),20)
        
        e1 = p2.episode_set.filter(title='CiudadanoKinders: Cómo hacer un monólogo')
        self.assertNotEqual(e1,[])
        
        e1 = e1[0]
        self.assertIsInstance(e1,Episode)

        self.assertEquals(e1.image,p2.image)
        
        # Clean copied image
        p2.image.delete()
        
        

class ParserRadiocoRSSLPTests(TestCase):


    def initialize_test(self):
        
        RSS_file = TEST_AUX_FILE_PATH + 'alegria_radioco.xml'
        feed_dict = feedparser.parse(RSS_file)
        
        return ParserRadioco(RSS_file),feed_dict 

    
    # get_entry_list from superclass
    def test_get_entry_list(self):
        
        rlp,fd = self.initialize_test()
        el = rlp.get_entry_list(fd)

        self.assertIsInstance(el,list)
        self.assertIsInstance(el[0],dict)


    def test_parse_program(self):

        program_web = 'https://cuacfm.org/radioco/programmes/alegria/'
        rlp,fd = self.initialize_test()
        
        p1 = rlp.parse_program(fd)
        
        self.assertEqual(p1.name,'Alegria')
        self.assertEqual(p1.language,'gl')
        self.assertEqual(p1.original_site,program_web)
        self.assertEqual(p1.rss_link_type,RADIOCO_TYPE[0])


    def test_parse_episode(self):
       
        rlp,fd = self.initialize_test()
        
        #Expected info
        exp_titlte = '15x22 Alegria'
        exp_pub_date = datetime.datetime(2018, 4, 24, 16, 0, tzinfo=pytz.utc)
        exp_file = 'https://cuacfm.org/radioco/recordings/2018-04-24%2018-00-00%20alegria.mp3'
        exp_web = 'https://cuacfm.org/radioco/programmes/alegria/15x22/'
        
        p1 = rlp.parse_program(fd)
        entry_dict = rlp.get_entry_list(fd)[0]
        
        e1 = rlp.parse_episode(entry_dict,p1)
        
        self.assertIsInstance(e1,Episode)
        self.assertEquals(e1.title,exp_titlte)
        self.assertEquals(e1.publication_date,exp_pub_date)
        self.assertEquals(e1.file,exp_file)
        self.assertEquals(e1.original_site,exp_web)
        self.assertIsNone(e1.original_id)



class ParserPodomaticRSSLPTests(TestCase):


    def initialize_test(self):
        
        RSS_file = TEST_AUX_FILE_PATH + 'falacalado_podomatic.xml'
        feed_dict = feedparser.parse(RSS_file)
        
        return ParserPodomatic(RSS_file),feed_dict 


    def test_parse_program(self):

        program_web = 'https://www.podomatic.com/podcasts/falacalado'
        rlp,fd = self.initialize_test()
        
        p1 = rlp.parse_program(fd)
        
        self.assertEqual(p1.name,"fala calado's podcast")
        self.assertEqual(p1.language,'gl')
        self.assertEqual(p1.original_site,program_web)
        self.assertEqual(p1.rss_link_type,PODOMATIC_TYPE[0])

    
    def test_parse_episode(self):
       
        rlp,fd = self.initialize_test()
        
        #Expected info
        exp_titlte = 'Un Falacalado moi Periscópico!'
        exp_pub_date = datetime.datetime(2010, 3, 14, 22, 12, 22, tzinfo=pytz.utc)
        exp_file = 'http://falacalado.podOmatic.com/enclosure/2010-03-14T15_12_22-07_00.mp3'
        exp_web = 'https://www.podomatic.com/podcasts/falacalado/episodes/2010-03-14T15_12_22-07_00'
        exp_original_id = 'http://falacalado.podomatic.com/entry/2010-03-14T15_12_22-07_00'
        
        p1 = rlp.parse_program(fd)
        entry_dict = rlp.get_entry_list(fd)[0]
        
        e1 = rlp.parse_episode(entry_dict,p1)
        
        self.assertIsInstance(e1,Episode)
        self.assertEquals(e1.title,exp_titlte)
        self.assertEquals(e1.publication_date,exp_pub_date)
        self.assertEquals(e1.file,exp_file)
        self.assertEquals(e1.original_site,exp_web)
        self.assertEquals(e1.original_id,exp_original_id)


class UpdateRSSDaemonTests(TestCase):

    
    def setUp(self):

        RSS_file = TEST_AUX_FILE_PATH + 'hasta-los-kinders_fewer_chapters.xml'
        u1 = User.objects.create(username='userRD1')
        rlp = ParserIvoox(RSS_file,u1)
        rlp.parse_and_save()
        
        
    def test_ud_iterate_program_table(self):
        
        p1 = Program.objects.get(name='Hasta Los Kinders')
        p1_id = p1.id
        
        self.assertEqual(p1.language,'Klingon')
        self.assertEqual(p1.author,'Autor Random')
        self.assertEqual(p1.image,Image.get_default_program_image())
        self.assertTrue(p1.tag_set.filter(name='humor'))
        self.assertEqual(p1.episode_set.count(),19)
        
        e1 = p1.episode_set.get(title='Las series japonesas')
        self.assertIsInstance(e1,Episode)
        e1_id = e1.id
        
        e4 = p1.episode_set.filter(title='CiudadanoKinders: Cómo hacer un monólogo')
        self.assertFalse(e4)
        
        RSS_file = TEST_AUX_FILE_PATH + 'hasta-los-kinders_original.xml'
        p1.rss_link = RSS_file
        p1.save()
        
        ud_iterate_program_table()
        
        p2 = Program.objects.get(pk=p1_id)
        
        self.assertEqual(p2.language,'es-ES')
        self.assertEqual(p2.author,'Fer Lee')
        self.assertNotEqual(p2.image,Image.get_default_program_image())
        self.assertTrue(p2.tag_set.filter(name='comedy'))
        self.assertEqual(p2.episode_set.count(),20)
        
        e2 = p2.episode_set.get(pk=e1_id)
        self.assertIsInstance(e2,Episode)
        self.assertEqual(e2.title,'Las series "anime" de HLK')
        
        e3 = p2.episode_set.filter(title='CiudadanoKinders: Cómo hacer un monólogo')
        self.assertTrue(e3)
        
        
