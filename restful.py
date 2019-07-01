import json
import os

import requests


class Test:
    """REST API test class.

    Usage example:

    restful.Test(
        "responses_dir",
        "samples_dir",
        "requests_dir",
        "errors_dir",
    ).run()"""

    def __init__(self, responses_dir, samples_dir, requests_dir, errors_dir, encoding="utf-8"):
        """Class initialization.

        :param responses_dir: directory for restful responses.
        :param samples_dir: directory for samples.
        :param requests_dir: directory for restful requests.
        :param errors_dir: directory for error output file.
        :param encoding: file open encoding."""

        # since init is the only place where this function will be used.
        def force_dir(directory):
            """Ensures directory."""
            if not os.path.exists(directory):
                os.makedirs(directory)

        force_dir(responses_dir)
        self._responses = responses_dir
        force_dir(samples_dir)
        self._samples = samples_dir
        self._requests = requests_dir
        force_dir(errors_dir)
        self._errors = errors_dir
        self._encoding = encoding

    def _get_request_content(self, name):
        """Reads request contents from a file.

        :param name: destination file name."""

        # complete file name.
        fn = os.path.join(self._requests, name + ".cnt")
        # GET requests usually don't have content part.
        if not os.path.exists(fn):
            return ""
        # return contents.
        return self._read_from_file(fn)

    def _save_to_file(self, fn, data, mode="w"):
        """Writes given data to a file.

        :param fn: destination file name.
        :param data: data to write.
        :param mode: write mode."""

        with open(fn, mode, encoding=self._encoding) as r:
            r.write(data)

    def _read_from_file(self, fn):
        """Reads data from a file.

        :param fn: source file name."""

        with open(fn, encoding=self._encoding) as f:
            return f.read()

    def _send_request(self, method, uri, headers, content, name):
        """Forms and sends request to given handler and write response to a file

        :param method: request method.
        :param uri: request URI.
        :param headers: request headers.
        :param content: request content.
        :param name: destination file name."""

        # establishes connection, forms and prepares a request then sends it.
        res = requests.Session().send(requests.Request(
            method, uri, headers=headers, data=content).prepare())
        res_content = res.content.decode(self._encoding)
        # save contents and headers to a file.
        self._save_to_file(
            os.path.join(self._responses, name + ".cnt"),
            res_content,
        )
        self._save_to_file(
            os.path.join(self._responses, name + ".snh"),
            json.dumps(
                {
                    "Status": res.status_code,
                    "Headers": dict(res.headers),
                },
                indent=4,
                sort_keys=True,
            ),
        )

        return res.status_code, res.headers, res_content

    def _check_sample_contents(self, name, res):
        """Compares response contents with a sample.

        :param name: destination file name.
        :param res: response contents."""

        # complete file name.
        sn = os.path.join(self._samples, name + ".cnt")
        rn = os.path.join(self._responses, name + ".cnt")
        # if sample not exists (i.e. first run), make it.
        if not os.path.exists(sn):
            self._save_to_file(sn, res)

            return True
        # compare result to sample, write an error if contents are not equal.
        return self._read_from_file(sn) == self._read_from_file(rn)

    def _check_sample_headers(self, name, status, headers):
        """Compares response headers and status code with a sample.

        :param name: destination sample file name.
        :param status: response status.
        :param headers: response headers."""

        # complete file name.
        sn = os.path.join(self._samples, name + ".snh")
        # if sample headers file does not exist, skip the check.
        if not os.path.exists(sn):
            return True
        # read request parameters.
        j = json.loads(self._read_from_file(sn))
        sample_status = j.get("Status")
        sample_headers = j.get("Headers")

        if sample_status is not None and sample_status != status:
            return False

        if sample_headers is None:
            return True

        for header, value in sample_headers.items():
            if headers.get(header) != value:
                return False

        return True

    def _get_names(self):
        """Iterates through request part files and get parameter names

        :rtype: list of file names"""

        # list files in directory and sort them by name.
        files = os.listdir(self._requests)
        files.sort()
        # iterate through files and select parameter names.
        return [file.rstrip(".prm") for file in files if ".prm" in file]

    def _parse_param(self, fn):
        """Compares response contents with a sample.

        :param fn: destination file name.
        :rtype: tuple of request type, URI and headers"""

        # read request parameters.
        j = json.loads(self._read_from_file(
            os.path.join(self._requests, fn + ".prm")))

        return j["Method"], j["URI"], j.get("Headers")

    def run(self):
        """Run tests, get results, compare them to samples and check for errors."""

        # at the start of a new test remove old errors.
        self._remove_errors()
        # iterate through file names, get corresponding data, do requests and compare results.
        for name in self._get_names():
            method, uri, headers = self._parse_param(name)
            req_content = self._get_request_content(name)
            res_status, res_headers, res_content = self._send_request(
                method, uri, headers, req_content, name)

            if not self._check_sample_headers(name, res_status, res_headers):
                self._write_err(name)

                continue

            if not self._check_sample_contents(name, res_content):
                self._write_err(name)

                continue

            print("Test #{} - OK".format(name))

    def _write_err(self, name):
        """Writes given error to errors.txt

        :param name: name of a test that contains an error."""

        # print to std out.
        msg = "Test #{} - FAIL\n".format(name)
        print(msg, end="")
        # append to file.
        self._save_to_file(os.path.join(self._errors, "errors.txt"), msg, "a")

    def _remove_errors(self):
        """Removes errors.txt if exist."""

        try:
            os.remove(os.path.join(self._errors, "errors.txt"))
        except OSError:
            pass
