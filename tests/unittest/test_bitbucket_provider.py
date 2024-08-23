from pr_agent.git_providers import BitbucketServerProvider
from pr_agent.git_providers.bitbucket_provider import BitbucketProvider
from unittest.mock import MagicMock
from atlassian.bitbucket import Bitbucket
from pr_agent.algo.types import EDIT_TYPE, FilePatchInfo


class TestBitbucketProvider:
    def test_parse_pr_url(self):
        url = "https://bitbucket.org/WORKSPACE_XYZ/MY_TEST_REPO/pull-requests/321"
        workspace_slug, repo_slug, pr_number = BitbucketProvider._parse_pr_url(url)
        assert workspace_slug == "WORKSPACE_XYZ"
        assert repo_slug == "MY_TEST_REPO"
        assert pr_number == 321


class TestBitbucketServerProvider:
    def test_parse_pr_url(self):
        url = "https://git.onpreminstance.com/projects/AAA/repos/my-repo/pull-requests/1"
        workspace_slug, repo_slug, pr_number = BitbucketServerProvider._parse_pr_url(url)
        assert workspace_slug == "AAA"
        assert repo_slug == "my-repo"
        assert pr_number == 1

    def mock_get_content_of_file(self, project_key, repository_slug, filename, at=None, markup=None):
        if at == '9c1cffdd9f276074bfb6fb3b70fbee62d298b058':
            return 'file\nwith\nsome\nlines\nto\nemulate\na\nreal\nfile\n'
        elif at == '2a1165446bdf991caf114d01f7c88d84ae7399cf':
            return 'file\nwith\nmultiple \nlines\nto\nemulate\na\nfake\nfile\n'
        elif at == 'f617708826cdd0b40abb5245eda71630192a17e3':
            return 'file\nwith\nmultiple \nlines\nto\nemulate\na\nreal\nfile\n'
        elif at == 'cb68a3027d6dda065a7692ebf2c90bed1bcdec28':
            return 'file\nwith\nsome\nchanges\nto\nemulate\na\nreal\nfile\n'
        elif at == '1905dcf16c0aac6ac24f7ab617ad09c73dc1d23b':
            return 'file\nwith\nsome\nlines\nto\nemulate\na\nfake\ntest\n'
        elif at == 'ae4eca7f222c96d396927d48ab7538e2ee13ca63':
            return 'readme\nwithout\nsome\nlines\nto\nsimulate\na\nreal\nfile'
        elif at == '548f8ba15abc30875a082156314426806c3f4d97':
            return 'file\nwith\nsome\nlines\nto\nemulate\na\nreal\nfile'
        return ''

    '''
    tests the 2-way diff functionality where the diff should be between the HEAD of branch b and node c
    NOT between the HEAD of main and the HEAD of branch b

          - o  branch b
         /
    o - o - o  main
        ^ node c
    '''

    def test_get_diff_files_simple_diverge(self):
        bitbucket_client = MagicMock(Bitbucket)
        bitbucket_client.get_pull_request.return_value = {
            'toRef': {'latestCommit': '9c1cffdd9f276074bfb6fb3b70fbee62d298b058'},
            'fromRef': {'latestCommit': '2a1165446bdf991caf114d01f7c88d84ae7399cf'}
        }
        bitbucket_client.get_pull_requests_commits.return_value = [
            {'id': '2a1165446bdf991caf114d01f7c88d84ae7399cf',
             'parents': [{'id': 'f617708826cdd0b40abb5245eda71630192a17e3'}]}
        ]
        bitbucket_client.get_commits.return_value = [
            {'id': '9c1cffdd9f276074bfb6fb3b70fbee62d298b058'},
            {'id': 'dbca09554567d2e4bee7f07993390153280ee450'}
        ]
        bitbucket_client.get_pull_requests_changes.return_value = [
            {
                'path': {'toString': 'Readme.md'},
                'type': 'MODIFY',
            }
        ]

        bitbucket_client.get_content_of_file.side_effect = self.mock_get_content_of_file

        provider = BitbucketServerProvider(
            "https://git.onpreminstance.com/projects/AAA/repos/my-repo/pull-requests/1",
            bitbucket_client=bitbucket_client
        )

        expected = [
            FilePatchInfo(
                'file\nwith\nmultiple \nlines\nto\nemulate\na\nreal\nfile\n',
                'file\nwith\nmultiple \nlines\nto\nemulate\na\nfake\nfile\n',
                '--- \n+++ \n@@ -5,5 +5,5 @@\n to\n emulate\n a\n-real\n+fake\n file\n',
                'Readme.md',
                edit_type=EDIT_TYPE.MODIFIED,
            )
        ]

        actual = provider.get_diff_files()

        assert actual == expected

    '''
    tests the 2-way diff functionality where the diff should be between the HEAD of branch b and node c
    NOT between the HEAD of main and the HEAD of branch b

          - o - o - o  branch b
         /     /  
    o - o -- o - o     main
             ^ node c
    '''

    def test_get_diff_files_diverge_with_merge_commit(self):
        bitbucket_client = MagicMock(Bitbucket)
        bitbucket_client.get_pull_request.return_value = {
            'toRef': {'latestCommit': 'cb68a3027d6dda065a7692ebf2c90bed1bcdec28'},
            'fromRef': {'latestCommit': '1905dcf16c0aac6ac24f7ab617ad09c73dc1d23b'}
        }
        bitbucket_client.get_pull_requests_commits.return_value = [
            {'id': '1905dcf16c0aac6ac24f7ab617ad09c73dc1d23b',
             'parents': [{'id': '692772f456c3db77a90b11ce39ea516f8c2bad93'}]},
            {'id': '692772f456c3db77a90b11ce39ea516f8c2bad93', 'parents': [
                {'id': '2a1165446bdf991caf114d01f7c88d84ae7399cf'},
                {'id': '9c1cffdd9f276074bfb6fb3b70fbee62d298b058'},
            ]},
            {'id': '2a1165446bdf991caf114d01f7c88d84ae7399cf',
             'parents': [{'id': 'f617708826cdd0b40abb5245eda71630192a17e3'}]}
        ]
        bitbucket_client.get_commits.return_value = [
            {'id': 'cb68a3027d6dda065a7692ebf2c90bed1bcdec28'},
            {'id': '9c1cffdd9f276074bfb6fb3b70fbee62d298b058'},
            {'id': 'dbca09554567d2e4bee7f07993390153280ee450'}
        ]
        bitbucket_client.get_pull_requests_changes.return_value = [
            {
                'path': {'toString': 'Readme.md'},
                'type': 'MODIFY',
            }
        ]

        bitbucket_client.get_content_of_file.side_effect = self.mock_get_content_of_file

        provider = BitbucketServerProvider(
            "https://git.onpreminstance.com/projects/AAA/repos/my-repo/pull-requests/1",
            bitbucket_client=bitbucket_client
        )

        expected = [
            FilePatchInfo(
                'file\nwith\nsome\nlines\nto\nemulate\na\nreal\nfile\n',
                'file\nwith\nsome\nlines\nto\nemulate\na\nfake\ntest\n',
                '--- \n+++ \n@@ -5,5 +5,5 @@\n to\n emulate\n a\n-real\n-file\n+fake\n+test\n',
                'Readme.md',
                edit_type=EDIT_TYPE.MODIFIED,
            )
        ]

        actual = provider.get_diff_files()

        assert actual == expected

    '''
    tests the 2-way diff functionality where the diff should be between the HEAD of branch c and node d
    NOT between the HEAD of main and the HEAD of branch c

            ---- o - o branch c
           /    /
          ---- o       branch b
         /    /  
        o - o - o      main
            ^ node d
    '''

    def test_get_diff_files_multi_merge_diverge(self):
        bitbucket_client = MagicMock(Bitbucket)
        bitbucket_client.get_pull_request.return_value = {
            'toRef': {'latestCommit': '9569922b22fe4fd0968be6a50ed99f71efcd0504'},
            'fromRef': {'latestCommit': 'ae4eca7f222c96d396927d48ab7538e2ee13ca63'}
        }
        bitbucket_client.get_pull_requests_commits.return_value = [
            {'id': 'ae4eca7f222c96d396927d48ab7538e2ee13ca63',
             'parents': [{'id': 'bbf300fb3af5129af8c44659f8cc7a526a6a6f31'}]},
            {'id': 'bbf300fb3af5129af8c44659f8cc7a526a6a6f31', 'parents': [
                {'id': '10b7b8e41cb370b48ceda8da4e7e6ad033182213'},
                {'id': 'd1bb183c706a3ebe4c2b1158c25878201a27ad8c'},
            ]},
            {'id': 'd1bb183c706a3ebe4c2b1158c25878201a27ad8c', 'parents': [
                {'id': '5bd76251866cb415fc5ff232f63a581e89223bda'},
                {'id': '548f8ba15abc30875a082156314426806c3f4d97'}
            ]},
            {'id': '5bd76251866cb415fc5ff232f63a581e89223bda',
             'parents': [{'id': '0e898cb355a5170d8c8771b25d43fcaa1d2d9489'}]},
            {'id': '10b7b8e41cb370b48ceda8da4e7e6ad033182213',
             'parents': [{'id': '0e898cb355a5170d8c8771b25d43fcaa1d2d9489'}]}
        ]
        bitbucket_client.get_commits.return_value = [
            {'id': '9569922b22fe4fd0968be6a50ed99f71efcd0504'},
            {'id': '548f8ba15abc30875a082156314426806c3f4d97'}
        ]
        bitbucket_client.get_pull_requests_changes.return_value = [
            {
                'path': {'toString': 'Readme.md'},
                'type': 'MODIFY',
            }
        ]

        bitbucket_client.get_content_of_file.side_effect = self.mock_get_content_of_file

        provider = BitbucketServerProvider(
            "https://git.onpreminstance.com/projects/AAA/repos/my-repo/pull-requests/1",
            bitbucket_client=bitbucket_client
        )

        expected = [
            FilePatchInfo(
                'file\nwith\nsome\nlines\nto\nemulate\na\nreal\nfile',
                'readme\nwithout\nsome\nlines\nto\nsimulate\na\nreal\nfile',
                '--- \n+++ \n@@ -1,9 +1,9 @@\n-file\n-with\n+readme\n+without\n some\n lines\n to\n-emulate\n+simulate\n a\n real\n file',
                'Readme.md',
                edit_type=EDIT_TYPE.MODIFIED,
            )
        ]

        actual = provider.get_diff_files()

        assert actual == expected
